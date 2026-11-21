"""Config-driven extraction: walks the output template of a document type and fills it.

* field (FieldSpec)   -> strategies tried in order on the current text region,
* container (dict)    -> each child filled from the same region,
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
    run_label,
    run_nth_match,
    run_regex,
    split_matches,
    split_sections,
)
from src.extraction.schema import DocumentType, FieldSpec, LabelStrategy, ListSpec, NthMatchStrategy, SectionSplit
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
    raw: str | None = None
    warnings: list[str] = []


class ExtractionResult(BaseModel):
    document_type: str
    data: dict[str, Any]
    """Output in the exact UZP JSON structure."""
    fields: dict[str, FieldTrace]
    """Per-field provenance, keyed by path ('przelew_bankowy.kwota', 'Zamawiajacy[1].nip')."""


def _candidates(spec: FieldSpec, lines: list[Line], stop: re.Pattern[str] | None):
    for index, strategy in enumerate(spec.extract, start=1):
        if isinstance(strategy, LabelStrategy):
            found = run_label(strategy, lines, spec.type, stop)
        elif isinstance(strategy, NthMatchStrategy):
            found = run_nth_match(strategy, lines, spec.type)
        else:
            found = run_regex(strategy, lines, spec.type)
        for candidate in found:
            yield index, candidate


def _check(spec: FieldSpec, value: Any) -> tuple[bool, str | None]:
    """(accept, warning) for the field's checksum policy."""
    checksum_name = spec.effective_checksum()
    if not checksum_name or not isinstance(value, str) or CHECKSUMS[checksum_name](value):
        return True, None
    message = f"invalid {checksum_name} checksum: {value}"
    return spec.on_invalid_checksum == "warn", message


def extract_field(
    spec: FieldSpec,
    lines: list[Line],
    stop: re.Pattern[str] | None,
    preset: tuple[str, Line, str] | None = None,
) -> FieldTrace:
    """`preset` = (raw value, line, detail) given by a list split (named regex group)."""
    normalize = VALUE_TYPES[spec.type].normalize
    rejected: list[str] = []

    if preset is not None and (value := normalize(preset[0])) is not None:
        accept, warning = _check(spec, value)
        if accept:
            return _trace(value, 0, Candidate(preset[0], preset[1].page, preset[1].text, preset[2]), [warning] if warning else [])
        rejected.append(warning)

    for index, candidate in _candidates(spec, lines, stop):
        value = normalize(candidate.raw)
        if value is None:
            continue
        accept, warning = _check(spec, value)
        if not accept:
            rejected.append(warning)
            continue
        return _trace(value, index, candidate, ([warning] if warning else []) + rejected)

    return FieldTrace(warnings=rejected)


def _trace(value: Any, index: int, candidate: Candidate, warnings: list[str]) -> FieldTrace:
    return FieldTrace(
        value=value,
        method="rule",
        rule=f"#{index} {candidate.detail}" if index else candidate.detail,
        page=candidate.page,
        snippet=candidate.snippet,
        raw=candidate.raw,
        warnings=warnings,
    )


def _is_empty(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_is_empty(v) for v in value.values())
    if isinstance(value, list):
        return all(_is_empty(v) for v in value)
    return value is None


class _Extractor:
    def __init__(self, doc_type: DocumentType, doc_lines: list[Line]):
        self.doc_type = doc_type
        self.doc_lines = doc_lines
        self.traces: dict[str, FieldTrace] = {}
        self._labels = self._collect_labels()
        self._stop_cache: dict[str, re.Pattern[str] | None] = {}

    def _collect_labels(self) -> dict[str, list[str]]:
        """Labels by field path ('a[].b') — used to stop search windows at other fields."""
        labels: dict[str, list[str]] = {}

        def walk(node: Any, prefix: str) -> None:
            if isinstance(node, FieldSpec):
                labels[prefix] = [l for s in node.extract if isinstance(s, LabelStrategy) for l in s.labels]
            elif isinstance(node, ListSpec):
                if isinstance(node.split, SectionSplit):
                    labels[f"{prefix}#split"] = node.split.start + node.split.end
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

    def build(self, node: Any, lines: list[Line], path: str, schema_path: str, presets: dict, item_detail: str) -> Any:
        if isinstance(node, FieldSpec):
            key = path.rsplit(".", 1)[-1]
            preset = (presets[key], lines[0], item_detail) if key in presets and lines else None
            trace = extract_field(node, lines, self._stop(schema_path), preset)
            self.traces[path] = trace
            return trace.value

        if isinstance(node, ListSpec):
            return self._build_list(node, lines, path, schema_path)

        return {
            key: self.build(
                child,
                lines,
                f"{path}.{key}" if path else key,
                f"{schema_path}.{key}" if schema_path else key,
                presets,
                item_detail,
            )
            for key, child in node.items()
        }

    def _build_list(self, spec: ListSpec, lines: list[Line], path: str, schema_path: str) -> list[Any]:
        if spec.split is None:
            return []
        region = self.doc_lines if spec.scope == "document" else lines
        if isinstance(spec.split, SectionSplit):
            item_texts = split_sections(spec.split, region)
        else:
            item_texts = split_matches(spec.split, region)

        items: list[Any] = []
        seen: set[tuple] = set()
        for item_text in item_texts:
            if len(items) >= spec.max_items:
                break
            index = len(items)
            before = set(self.traces)
            value = self.build(spec.item, item_text.lines, f"{path}[{index}]", f"{schema_path}[]", item_text.presets, item_text.detail)
            key = tuple(value.get(k) for k in spec.unique_by) if spec.unique_by and isinstance(value, dict) else None
            if _is_empty(value) or (key is not None and key in seen):
                for new in set(self.traces) - before:  # discard traces of a dropped item
                    del self.traces[new]
                continue
            if key is not None:
                seen.add(key)
            items.append(value)
        return items


def extract(doc: IngestedDocument, doc_type: DocumentType) -> ExtractionResult:
    lines = document_lines(doc)
    extractor = _Extractor(doc_type, lines)
    data = extractor.build(doc_type.output, lines, "", "", {}, "")
    return ExtractionResult(document_type=doc_type.name, data=data, fields=extractor.traces)
