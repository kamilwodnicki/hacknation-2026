"""Config-driven extraction: walks the output template of a document type and fills it.

* field (FieldSpec)   -> strategies tried in order on the current text region,
* container (dict)    -> children filled from the same region; fields depending on other
                         fields (derived / lookup) are filled last, from their siblings,
* list (ListSpec)     -> the region is split into item regions, each filled from the item template.
"""

import re
from typing import Any

from pydantic import BaseModel

from src.extraction.rules import (
    Candidate,
    Line,
    compile_labels,
    document_lines,
    run_keyword_map,
    run_label,
    run_nth_match,
    run_regex,
    split_matches,
    split_sections,
    split_whole,
)
from src.extraction.schema import (
    DerivedStrategy,
    DocumentType,
    FieldSpec,
    KeywordMapStrategy,
    LabelStrategy,
    ListSpec,
    LookupStrategy,
    MatchesSplit,
    NthMatchStrategy,
    RegexStrategy,
    SectionSplit,
)
from src.ingestion import IngestedDocument
from src.validation.checksums import CHECKSUMS
from src.validation.normalizers import VALUE_TYPES


class FieldTrace(BaseModel):
    """Where a value came from — shown to the user for transparency."""

    value: Any = None
    method: str | None = None
    """'rule' (later also 'llm'); None when nothing was found."""
    rule: str | None = None
    page: int | None = None
    snippet: str | None = None
    raw: Any = None
    warnings: list[str] = []
    trusted: bool = False
    """Found by a strategy marked `trusted` — hybrid mode keeps it."""


class ExtractionResult(BaseModel):
    document_type: str
    data: dict[str, Any]
    """Output in the exact UZP JSON structure."""
    fields: dict[str, FieldTrace]
    """Per-field provenance, keyed by path ('przelew_bankowy.kwota', 'Zamawiajacy[1].nip')."""


def _check(spec: FieldSpec, value: Any) -> tuple[bool, str | None]:
    """(accept, warning) for the field's checksum policy."""
    checksum_name = spec.effective_checksum()
    if not checksum_name or not isinstance(value, str) or CHECKSUMS[checksum_name](value):
        return True, None
    message = f"invalid {checksum_name} checksum: {value}"
    return spec.on_invalid_checksum == "warn", message


def _resolve(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for key in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _lookup(dictionary: dict[Any, Any], key: Any) -> Any:
    if key is None:
        return None
    for candidate in (key, str(key), int(key) if str(key).isdigit() else None):
        if candidate is not None and candidate in dictionary:
            return dictionary[candidate]
    return None


def _trace(value: Any, rule: str, candidate: Candidate | None, warnings: list[str]) -> FieldTrace:
    return FieldTrace(
        value=value,
        method="rule",
        rule=rule,
        page=candidate.page if candidate else None,
        snippet=(candidate.snippet or None) if candidate else None,
        raw=candidate.raw if candidate else None,
        warnings=warnings,
    )


class _Extractor:
    def __init__(self, doc_type: DocumentType, doc_lines: list[Line]):
        self.doc_type = doc_type
        self.doc_lines = doc_lines
        self.traces: dict[str, FieldTrace] = {}
        self._labels = self._collect_labels()
        self._stop_cache: dict[str, re.Pattern[str] | None] = {}
        self._document_seen: dict[str, set[tuple]] = {}
        """Keys already used by document-scope lists, per schema path (shared by all parents)."""

    # --- stop labels -------------------------------------------------------------------

    def _collect_labels(self) -> dict[str, list[str]]:
        """Labels by field path ('a[].b') — used to stop search windows at other fields."""
        labels: dict[str, list[str]] = {}

        def walk(node: Any, prefix: str) -> None:
            if isinstance(node, FieldSpec):
                labels[prefix] = [l for s in node.extract if isinstance(s, LabelStrategy) for l in s.labels]
            elif isinstance(node, ListSpec):
                for split in node.splits():
                    if isinstance(split, SectionSplit):
                        labels.setdefault(f"{prefix}#split", []).extend(split.start + split.end)
                walk(node.item, f"{prefix}[]")
            else:
                for key, child in node.items():
                    walk(child, f"{prefix}.{key}" if prefix else key)

        walk(self.doc_type.output, "")
        return labels

    def _stop(self, schema_path: str) -> re.Pattern[str] | None:
        if schema_path not in self._stop_cache:
            labels = list(self.doc_type.stop_labels)
            for path, field_labels in self._labels.items():
                if path != schema_path:
                    labels.extend(field_labels)
            self._stop_cache[schema_path] = compile_labels(labels) if labels else None
        return self._stop_cache[schema_path]

    # --- fields --------------------------------------------------------------------------

    def _field(
        self,
        spec: FieldSpec,
        lines: list[Line],
        schema_path: str,
        preset: tuple[str, Line, str] | None,
        context: dict[str, Any],
    ) -> FieldTrace:
        normalize = VALUE_TYPES[spec.type].normalize
        rejected: list[str] = []

        def accept(value: Any, rule: str, candidate: Candidate | None) -> FieldTrace | None:
            if reason := spec.plausible(value):
                rejected.append(reason)
                return None
            ok, warning = _check(spec, value)
            if not ok:
                rejected.append(warning)
                return None
            return _trace(value, rule, candidate, ([warning] if warning else []) + rejected)

        if preset is not None and (value := normalize(preset[0])) is not None:
            if trace := accept(value, preset[2], Candidate(preset[0], preset[1].page, preset[1].text, preset[2])):
                return trace

        stop = self._stop(schema_path)
        for index, strategy in enumerate(spec.extract, start=1):
            if isinstance(strategy, DerivedStrategy):
                present = _resolve(context, strategy.source) not in (None, "", [])
                value = strategy.if_present if present else strategy.if_absent
                if value is not None:
                    return _trace(value, f"#{index} derived from {strategy.source}", None, rejected)
                continue
            if isinstance(strategy, LookupStrategy):
                key = _resolve(context, strategy.source)
                value = _lookup(self.doc_type.dictionary(strategy.dictionary), key)
                if value is not None:
                    return _trace(value, f"#{index} {strategy.dictionary}[{key}]", None, rejected)
                continue

            if isinstance(strategy, KeywordMapStrategy):
                for candidate in run_keyword_map(strategy, lines):
                    trace = _trace(candidate.raw, f"#{index} {candidate.detail}", candidate, rejected)
                    trace.trusted = strategy.trusted
                    return trace
                continue

            if isinstance(strategy, LabelStrategy):
                found = run_label(strategy, lines, spec.type, stop)
            elif isinstance(strategy, NthMatchStrategy):
                found = run_nth_match(strategy, lines, spec.type)
            else:
                assert isinstance(strategy, RegexStrategy)
                found = run_regex(strategy, lines, spec.type)
            for candidate in found:
                value = normalize(candidate.raw)
                if value is not None and (trace := accept(value, f"#{index} {candidate.detail}", candidate)):
                    trace.trusted = strategy.trusted
                    return trace

        return FieldTrace(warnings=rejected)

    # --- template walk -------------------------------------------------------------------

    def build(self, node: Any, lines: list[Line], path: str, schema_path: str, presets: dict, item_detail: str) -> Any:
        if isinstance(node, ListSpec):
            return self._build_list(node, lines, path, schema_path)
        if isinstance(node, FieldSpec):  # a bare field at the top of a list item
            return self._build_container({"": node}, lines, path, schema_path, presets, item_detail)[""]
        return self._build_container(node, lines, path, schema_path, presets, item_detail)

    def _build_container(
        self, node: dict, lines: list[Line], path: str, schema_path: str, presets: dict, item_detail: str
    ) -> dict:
        def child_paths(key: str) -> tuple[str, str]:
            if not key:
                return path, schema_path
            return (f"{path}.{key}" if path else key), (f"{schema_path}.{key}" if schema_path else key)

        result: dict[str, Any] = {key: None for key in node}
        dependent = [k for k, c in node.items() if isinstance(c, FieldSpec) and c.is_dependent]
        for key, child in node.items():
            if key in dependent:
                continue
            p, sp = child_paths(key)
            if isinstance(child, FieldSpec):
                preset = (presets[key], lines[0], item_detail) if key in presets and lines else None
                trace = self._field(child, lines, sp, preset, result)
                self.traces[p] = trace
                result[key] = trace.value
            else:
                result[key] = self.build(child, lines, p, sp, presets, item_detail)
        for key in dependent:
            p, sp = child_paths(key)
            trace = self._field(node[key], lines, sp, None, result)
            self.traces[p] = trace
            result[key] = trace.value
        return result

    def _build_list(self, spec: ListSpec, lines: list[Line], path: str, schema_path: str) -> list[Any]:
        region = self.doc_lines if spec.scope == "document" else lines
        item_texts = []
        for split in spec.splits():
            if isinstance(split, SectionSplit):
                item_texts = split_sections(split, region)
            elif isinstance(split, MatchesSplit):
                item_texts = split_matches(split, region)
            else:
                item_texts = split_whole(split, region)
            if item_texts:
                break

        items: list[Any] = []
        seen: set[tuple] = self._document_seen.setdefault(schema_path, set()) if spec.scope == "document" else set()
        for item_text in item_texts:
            if len(items) >= spec.max_items:
                break
            before = set(self.traces)
            value = self.build(
                spec.item, item_text.lines, f"{path}[{len(items)}]", f"{schema_path}[]", item_text.presets, item_text.detail
            )
            key = tuple(_resolve(value, k) for k in spec.unique_by) if spec.unique_by and isinstance(value, dict) else None
            if key is not None and all(k is None for k in key):
                key = None  # identifying fields not found: cannot tell duplicates apart
            new_traces = [self.traces[p] for p in set(self.traces) - before]
            # An item counts only if something was found in its text (not just derived/defaults).
            found = any(
                t.value is not None and t.rule and "derived from" not in t.rule and "default value" not in t.rule
                for t in new_traces
            )
            if not found or _is_empty(value) or (key is not None and key in seen):
                for new in set(self.traces) - before:  # discard traces of a dropped item
                    del self.traces[new]
                continue
            if key is not None:
                seen.add(key)
            items.append(value)
        return items


def _is_empty(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_is_empty(v) for v in value.values())
    if isinstance(value, list):
        return all(_is_empty(v) for v in value)
    return value is None


def _dependent_trace(spec: FieldSpec, context: dict[str, Any], doc_type: DocumentType) -> FieldTrace:
    for index, strategy in enumerate(spec.extract, start=1):
        if isinstance(strategy, DerivedStrategy):
            present = _resolve(context, strategy.source) not in (None, "", [])
            value = strategy.if_present if present else strategy.if_absent
            if value is not None:
                return _trace(value, f"#{index} derived from {strategy.source}", None, [])
        elif isinstance(strategy, LookupStrategy):
            key = _resolve(context, strategy.source)
            value = _lookup(doc_type.dictionary(strategy.dictionary), key)
            if value is not None:
                return _trace(value, f"#{index} {strategy.dictionary}[{key}]", None, [])
    return FieldTrace()


def apply_dependents(doc_type: DocumentType, data: dict[str, Any], traces: dict[str, FieldTrace]) -> None:
    """Recompute derived / lookup fields of already filled data (e.g. after merging LLM values)."""

    def walk(node: Any, value: Any, path: str) -> None:
        if isinstance(node, ListSpec):
            for i, item in enumerate(value or []):
                walk(node.item, item, f"{path}[{i}]")
            return
        if not isinstance(node, dict) or not isinstance(value, dict):
            return
        dependent = []
        for key, child in node.items():
            child_path = f"{path}.{key}" if path else key
            if isinstance(child, FieldSpec):
                if child.is_dependent:
                    dependent.append((key, child, child_path))
            else:
                walk(child, value.get(key), child_path)
        for key, child, child_path in dependent:
            trace = _dependent_trace(child, value, doc_type)
            value[key] = trace.value
            traces[child_path] = trace

    walk(doc_type.output, data, "")


def extract(doc: IngestedDocument, doc_type: DocumentType) -> ExtractionResult:
    lines = document_lines(doc)
    extractor = _Extractor(doc_type, lines)
    data = extractor.build(doc_type.output, lines, "", "", {}, "")
    return ExtractionResult(document_type=doc_type.name, data=data, fields=extractor.traces)
