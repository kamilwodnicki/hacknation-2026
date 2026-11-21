"""Run the pipeline on a labelled dataset and aggregate field-level scores."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from src.evaluation.metrics import Counts, Mismatch, compare
from src.extraction import DocumentType, extract
from src.ingestion import read_pdf


class DatasetDocument(BaseModel):
    pdf: str
    reference: str
    document_type: str


class Dataset(BaseModel):
    name: str
    data_dir: str = "."
    cases: str
    documents: list[DatasetDocument]


def load_dataset(path: Path) -> Dataset:
    return Dataset.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


@dataclass
class TypeReport:
    documents: int = 0
    defined: bool = True
    """False when no YAML definition exists yet (all reference values count as FN)."""
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
class EvaluationReport:
    dataset: str
    types: dict[str, TypeReport]
    missing_files: list[str]

    def total(self, lenient: bool = False) -> Counts:
        total = Counts()
        for report in self.types.values():
            total += report.total(lenient)
        return total


def _load_reference(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig").strip()
    return json.loads(text) if text else {}


def evaluate(dataset: Dataset, data_root: Path, document_types: dict[str, DocumentType]) -> EvaluationReport:
    base = data_root / dataset.data_dir
    reports: dict[str, TypeReport] = {}
    missing: list[str] = []

    for case in sorted(p for p in base.glob(dataset.cases) if p.is_dir()):
        for item in dataset.documents:
            pdf, ref_path = case / item.pdf, case / item.reference
            if not pdf.exists() or not ref_path.exists():
                missing.append(str((pdf if not pdf.exists() else ref_path).relative_to(base)))
                continue
            report = reports.setdefault(item.document_type, TypeReport())
            report.documents += 1

            doc_type = document_types.get(item.document_type)
            report.defined = doc_type is not None
            predicted = extract(read_pdf(pdf), doc_type).data if doc_type else {}
            comparison = compare(predicted, _load_reference(ref_path))

            for target, source in ((report.strict, comparison.strict), (report.lenient, comparison.lenient)):
                for path, counts in source.items():
                    target.setdefault(path, Counts())
                    target[path] += counts
            report.errors.extend((case.name, m) for m in comparison.mismatches)

    return EvaluationReport(dataset=dataset.name, types=reports, missing_files=missing)
