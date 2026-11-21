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
class EvaluationReport:
    dataset: str
    oracle: bool
    """True = extraction used the expected type instead of the classifier."""
    types: dict[str, TypeReport]
    classifications: list[ClassificationOutcome]
    missing_files: list[str]

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


def evaluate(
    dataset: Dataset,
    data_root: Path,
    document_types: dict[str, DocumentType],
    oracle: bool = False,
) -> EvaluationReport:
    base = data_root / dataset.data_dir
    reports: dict[str, TypeReport] = {}
    outcomes: list[ClassificationOutcome] = []
    missing: list[str] = []

    for case in sorted(p for p in base.glob(dataset.cases) if p.is_dir()):
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
            predicted = extract(doc, used_type).data if used_type else {}
            comparison = compare(predicted, _load_reference(ref_path), dataset.fuzzy_paths())

            for target, source in ((report.exact, comparison.exact), (report.uzp, comparison.uzp)):
                for path, counts in source.items():
                    target.setdefault(path, Counts())
                    target[path] += counts
            report.errors.extend((case.name, m) for m in comparison.mismatches)

    for extra in dataset.extra:
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
        dataset=dataset.name, oracle=oracle, types=reports, classifications=outcomes, missing_files=missing
    )
