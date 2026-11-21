"""Run the pipeline on a labelled dataset and aggregate field-level scores."""

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from src.classification import classify
from src.evaluation.metrics import Counts, Mismatch, compare
from src.extraction import DocumentType, extract
from src.ingestion import IngestionError, read_pdf
from src.llm.extractor import build_messages, has_gaps
from src.pipeline import LLMInfo, extract_with_llm


class DatasetDocument(BaseModel):
    pdf: str
    reference: str
    document_type: str


class ExtraDocument(BaseModel):
    """A document checked for classification only (no reference JSON)."""

    pdf: str
    """Path relative to the data root."""
    document_type: str | None
    """Expected type; None = must not be recognized (empty JSON)."""


class Dataset(BaseModel):
    name: str
    data_dir: str = "."
    cases: str
    documents: list[DatasetDocument]
    extra: list[ExtraDocument] = []
    fuzzy_fields: list[str] = []
    """Paths of "long string" fields compared by similarity in the uzp metric."""
    fuzzy_threshold: float = 0.8

    def fuzzy_paths(self) -> dict[str, float]:
        return {path: self.fuzzy_threshold for path in self.fuzzy_fields}


def load_dataset(path: Path) -> Dataset:
    return Dataset.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


@dataclass
class TypeReport:
    documents: int = 0
    defined: bool = True
    """False when the YAML definition has no output fields yet (all values count as FN)."""
    exact: dict[str, Counts] = field(default_factory=dict)
    uzp: dict[str, Counts] = field(default_factory=dict)
    errors: list[tuple[str, Mismatch]] = field(default_factory=list)
    """(case name, mismatch)"""

    def total(self, mode: str = "uzp") -> Counts:
        total = Counts()
        for counts in getattr(self, mode).values():
            total += counts
        return total


@dataclass
class ClassificationOutcome:
    document: str
    expected: str | None
    predicted: str | None
    reason: str


@dataclass
class LLMStats:
    documents_sent: int = 0
    cached: int = 0
    errors: int = 0
    skipped: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, info: LLMInfo) -> None:
        if info.used:
            self.documents_sent += 1
            self.cached += info.cached
            if not info.cached:
                self.input_tokens += info.input_tokens or 0
                self.output_tokens += info.output_tokens or 0
        elif info.error:
            self.errors += 1
        elif info.skipped_reason:
            self.skipped += 1


@dataclass
class EvaluationReport:
    dataset: str
    oracle: bool
    """True = extraction used the expected type instead of the classifier."""
    types: dict[str, TypeReport]
    classifications: list[ClassificationOutcome]
    missing_files: list[str]
    mode: str = "rules"
    llm: LLMStats = field(default_factory=LLMStats)

    def total(self, mode: str = "uzp") -> Counts:
        total = Counts()
        for report in self.types.values():
            total += report.total(mode)
        return total

    def confusion(self) -> Counter[tuple[str | None, str | None]]:
        return Counter((c.expected, c.predicted) for c in self.classifications)

    @property
    def classification_accuracy(self) -> float:
        if not self.classifications:
            return 0.0
        return sum(c.expected == c.predicted for c in self.classifications) / len(self.classifications)


def _load_reference(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig").strip()
    return json.loads(text) if text else {}


def _cases(dataset: Dataset, data_root: Path, limit: int | None, only: list[str] | None) -> list[Path]:
    base = data_root / dataset.data_dir
    cases = sorted(p for p in base.glob(dataset.cases) if p.is_dir())
    if only:
        cases = [c for c in cases if c.name in only]
    return cases[:limit] if limit else cases


def evaluate(
    dataset: Dataset,
    data_root: Path,
    document_types: dict[str, DocumentType],
    oracle: bool = False,
    mode: str = "rules",
    limit: int | None = None,
    only: list[str] | None = None,
) -> EvaluationReport:
    """`mode`: rules / llm / hybrid. `limit` / `only` restrict the cases (cheap LLM trials)."""
    base = data_root / dataset.data_dir
    reports: dict[str, TypeReport] = {}
    outcomes: list[ClassificationOutcome] = []
    missing: list[str] = []
    llm_stats = LLMStats()

    for case in _cases(dataset, data_root, limit, only):
        for item in dataset.documents:
            pdf, ref_path = case / item.pdf, case / item.reference
            if not pdf.exists() or not ref_path.exists():
                missing.append(str((pdf if not pdf.exists() else ref_path).relative_to(base)))
                continue
            report = reports.setdefault(item.document_type, TypeReport())
            report.documents += 1
            expected_type = document_types.get(item.document_type)
            report.defined = bool(expected_type and expected_type.fields())

            doc = read_pdf(pdf)
            result = classify(doc, document_types)
            outcomes.append(
                ClassificationOutcome(f"{case.name}/{item.pdf}", item.document_type, result.document_type, result.reason)
            )
            used_type = expected_type if oracle else document_types.get(result.document_type or "")
            predicted = {}
            if used_type:
                extraction, info = extract_with_llm(doc, used_type, mode=mode)
                predicted = extraction.data
                llm_stats.add(info)
            comparison = compare(predicted, _load_reference(ref_path), dataset.fuzzy_paths())

            for target, source in ((report.exact, comparison.exact), (report.uzp, comparison.uzp)):
                for path, counts in source.items():
                    target.setdefault(path, Counts())
                    target[path] += counts
            report.errors.extend((case.name, m) for m in comparison.mismatches)

    for extra in ([] if limit or only or len(dataset.documents) < 3 else dataset.extra):
        pdfs = sorted(data_root.glob(extra.pdf)) if any(c in extra.pdf for c in "*?[") else [data_root / extra.pdf]
        for pdf in pdfs:
            if not pdf.exists():
                missing.append(extra.pdf)
                continue
            try:
                result = classify(read_pdf(pdf), document_types)
                predicted, reason = result.document_type, result.reason
            except IngestionError as exc:
                predicted, reason = None, f"unreadable: {exc}"
            name = str(pdf.relative_to(data_root)).replace("\\", "/")
            outcomes.append(ClassificationOutcome(name, extra.document_type, predicted, reason))

    return EvaluationReport(
        dataset=dataset.name,
        oracle=oracle,
        types=reports,
        classifications=outcomes,
        missing_files=missing,
        mode=mode,
        llm=llm_stats,
    )


def estimate_llm(
    dataset: Dataset,
    data_root: Path,
    document_types: dict[str, DocumentType],
    mode: str,
    max_chars: int,
    limit: int | None = None,
    only: list[str] | None = None,
) -> dict[str, int]:
    """How many documents would be sent to the model and roughly how many tokens — no API call."""
    documents = sent = input_chars = 0
    for case in _cases(dataset, data_root, limit, only):
        for item in dataset.documents:
            pdf = case / item.pdf
            if not pdf.exists():
                continue
            documents += 1
            doc = read_pdf(pdf)
            doc_type = document_types.get(classify(doc, document_types).document_type or "")
            if doc_type is None:
                continue
            if mode == "hybrid" and not has_gaps(extract(doc, doc_type), doc_type):
                continue
            sent += 1
            input_chars += sum(len(m["content"]) for m in build_messages(doc, doc_type, max_chars))
    # ~3.5 characters per token (Google/Mistral docs); output ~600 tokens per document.
    return {"documents": documents, "sent": sent, "input_tokens": int(input_chars / 3.5), "output_tokens": sent * 600}
