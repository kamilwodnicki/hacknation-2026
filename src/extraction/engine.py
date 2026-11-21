"""Config-driven extraction: runs the strategies of every field defined in a document type."""

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
)
from src.extraction.schema import DocumentType, FieldSpec, LabelStrategy, NthMatchStrategy
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
    """Per-field provenance, keyed by dotted path (e.g. 'przelew_bankowy.kwota')."""


def _stop_pattern(doc_type: DocumentType, current: str) -> re.Pattern[str] | None:
    """Labels of all *other* fields + document stop labels end a value's search window."""
    labels = list(doc_type.stop_labels)
    for path, spec in doc_type.fields().items():
        if path == current:
            continue
        for strategy in spec.extract:
            if isinstance(strategy, LabelStrategy):
                labels.extend(strategy.labels)
    return compile_labels(labels) if labels else None


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


def extract_field(spec: FieldSpec, lines: list[Line], stop: re.Pattern[str] | None) -> FieldTrace:
    normalize = VALUE_TYPES[spec.type].normalize
    checksum_name = spec.effective_checksum()
    rejected: list[str] = []

    for index, candidate in _candidates(spec, lines, stop):
        value = normalize(candidate.raw)
        if value is None:
            continue
        warnings: list[str] = []
        if checksum_name and isinstance(value, str) and not CHECKSUMS[checksum_name](value):
            message = f"invalid {checksum_name} checksum: {value}"
            if spec.on_invalid_checksum == "reject":
                rejected.append(message)
                continue
            warnings.append(message)
        return _trace(value, index, candidate, warnings + rejected)

    return FieldTrace(warnings=rejected)


def _trace(value: Any, index: int, candidate: Candidate, warnings: list[str]) -> FieldTrace:
    return FieldTrace(
        value=value,
        method="rule",
        rule=f"#{index} {candidate.detail}",
        page=candidate.page,
        snippet=candidate.snippet,
        raw=candidate.raw,
        warnings=warnings,
    )


def _build(template: Any, values: dict[str, Any], prefix: str = "") -> Any:
    if isinstance(template, FieldSpec):
        return values.get(prefix)
    return {key: _build(child, values, f"{prefix}.{key}" if prefix else key) for key, child in template.items()}


def extract(doc: IngestedDocument, doc_type: DocumentType) -> ExtractionResult:
    lines = document_lines(doc)
    traces = {
        path: extract_field(spec, lines, _stop_pattern(doc_type, path))
        for path, spec in doc_type.fields().items()
    }
    data = _build(doc_type.output, {path: trace.value for path, trace in traces.items()})
    return ExtractionResult(document_type=doc_type.name, data=data, fields=traces)
