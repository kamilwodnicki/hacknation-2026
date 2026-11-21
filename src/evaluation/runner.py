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
from src.ingestion import read_pdf


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


def load_dataset(path: Path) -> Dataset:
    return Dataset.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


@dataclass
class TypeReport:
    documents: int = 0
    defined: bool = True
    """False when the YAML definition has no output fields yet (all values count as FN)."""
    strict: dict[str, Counts] = field(default_factory=dict)
    lenient: dict[str, Counts] = field(default_factory=dict)
    errors: list[tuple[str, Mismatch]] = field(default_factory=list)
    """(case name, mismatch)"""

    def total(self, lenient: bool = False) -> Counts:
        total = Counts()
        for counts in (self.lenient if lenient else self.strict).values():
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

    def total(self, lenient: bool = False) -> Counts:
        total = Counts()
        for report in self.types.values():
            total += report.total(lenient)
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
            comparison = compare(predicted, _load_reference(ref_path))

            for target, source in ((report.strict, comparison.strict), (report.lenient, comparison.lenient)):
                for path, counts in source.items():
                    target.setdefault(path, Counts())
                    target[path] += counts
            report.errors.extend((case.name, m) for m in comparison.mismatches)

    for extra in dataset.extra:
        pdf = data_root / extra.pdf
        if not pdf.exists():
            missing.append(extra.pdf)
            continue
        result = classify(read_pdf(pdf), document_types)
        outcomes.append(ClassificationOutcome(extra.pdf, extra.document_type, result.document_type, result.reason))

    return EvaluationReport(
        dataset=dataset.name, oracle=oracle, types=reports, classifications=outcomes, missing_files=missing
    )
