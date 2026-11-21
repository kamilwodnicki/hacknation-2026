"""Rule-based document classification driven by the `classification` section of each YAML."""

import re

from pydantic import BaseModel

from src.extraction.schema import DocumentType
from src.ingestion import IngestedDocument, PageSource
from src.validation.normalizers import fold


def _title_form(line: str) -> str:
    line = line.strip()
    # Letter-spaced headings: "P E Ł N O M O C N I C T W O" -> "PEŁNOMOCNICTWO"
    if re.fullmatch(r"(?:\w\s+){3,}\w", line):
        line = re.sub(r"\s+", "", line)
    return fold(re.sub(r"[^\w\s]", " ", line))


class TypeScore(BaseModel):
    score: int
    keywords: list[str]
    title: str | None = None
    excluded_by: str | None = None


class ClassificationResult(BaseModel):
    document_type: str | None
    """None = not recognized: the output JSON is empty."""
    reason: str
    scores: dict[str, TypeScore]


def score_type(doc: IngestedDocument, doc_type: DocumentType) -> TypeScore:
    rules = doc_type.classification
    pages = [p for p in doc.pages if p.source != PageSource.SKIPPED][: rules.pages]
    body = fold("\n".join(p.text for p in pages))
    header = [line for p in pages for line in p.text.split("\n") if line.strip()][: rules.header_lines]

    keywords = [k for k in rules.keywords if fold(k) in body]
    titles = {_title_form(t): t for t in rules.titles}
    title = next((titles[_title_form(line)] for line in header if _title_form(line) in titles), None)
    header_text = fold("\n".join(header))
    excluded_by = next((e for e in rules.exclude if fold(e) in header_text), None)

    return TypeScore(
        score=len(keywords) + (rules.title_weight if title else 0),
        keywords=keywords,
        title=title,
        excluded_by=excluded_by,
    )


def classify(doc: IngestedDocument, document_types: dict[str, DocumentType]) -> ClassificationResult:
    scores = {name: score_type(doc, t) for name, t in document_types.items()}
    candidates = sorted(
        (
            (s.score, name)
            for name, s in scores.items()
            if s.excluded_by is None and s.score >= document_types[name].classification.min_score
        ),
        reverse=True,
    )
    if not candidates:
        return ClassificationResult(document_type=None, reason="no type reached its min_score", scores=scores)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        tied = ", ".join(name for score, name in candidates if score == candidates[0][0])
        return ClassificationResult(document_type=None, reason=f"tie between: {tied}", scores=scores)
    best_score, best = candidates[0]
    return ClassificationResult(document_type=best, reason=f"rules (score {best_score})", scores=scores)
