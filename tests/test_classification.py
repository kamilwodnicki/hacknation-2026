import os
from pathlib import Path

import pytest

from src.classification import classify
from src.config import Settings
from src.classification.classifier import _title_form, fold
from src.extraction import DocumentType, load_document_types
from src.ingestion import IngestedDocument, Page, PageSource, read_pdf
from tests.conftest import transfer_pdf

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
TEMPLATE = DATA_DIR / "szablon-aplikacja" / "input" / "case1"


def doc(*pages: str, source: PageSource = PageSource.TEXT_LAYER) -> IngestedDocument:
    return IngestedDocument(
        filename="t.pdf", pages=[Page(number=i, text=t, source=source) for i, t in enumerate(pages, start=1)]
    )


def types(**classifications) -> dict[str, DocumentType]:
    return {name: DocumentType.model_validate({"name": name, "classification": c}) for name, c in classifications.items()}


def test_fold_ignores_case_whitespace_and_polish_letters():
    assert fold("Pełnomocnictwo  PRZYJMUJĘ") == "pelnomocnictwo przyjmuje"
    assert fold("ŁÓDŹ") == "lodz"


def test_letter_spaced_heading_is_joined():
    assert _title_form("P E Ł N O M O C N I C T W O") == "pelnomocnictwo"
    assert _title_form("ODWOŁANIE:") == "odwolanie"
    assert _title_form("a b") == "a b"  # too short to be a spaced heading


def test_highest_score_wins_and_title_adds_weight():
    t = types(
        a={"keywords": ["alfa", "beta"], "min_score": 1},
        b={"keywords": ["gamma"], "titles": ["Nagłówek B"], "min_score": 1},
    )
    assert classify(doc("alfa beta gamma"), t).document_type == "a"
    assert classify(doc("NAGŁÓWEK B\nalfa beta gamma"), t).document_type == "b"


def test_below_min_score_is_not_recognized():
    t = types(a={"keywords": ["alfa", "beta"], "min_score": 2})
    result = classify(doc("tylko alfa"), t)
    assert result.document_type is None
    assert result.scores["a"].keywords == ["alfa"]


def test_tie_is_not_recognized():
    t = types(a={"keywords": ["wspólne"], "min_score": 1}, b={"keywords": ["wspólne"], "min_score": 1})
    result = classify(doc("wspólne słowo"), t)
    assert result.document_type is None
    assert "tie" in result.reason


def test_exclude_phrase_in_header_disqualifies():
    t = types(a={"keywords": ["odwołujący"], "exclude": ["odpowiedź na odwołanie"], "min_score": 1})
    assert classify(doc("ODPOWIEDŹ NA ODWOŁANIE\nOdwołujący: X"), t).document_type is None
    assert classify(doc("ODWOŁANIE\nOdwołujący: X"), t).document_type == "a"


def test_only_first_pages_are_used():
    t = types(a={"keywords": ["alfa"], "min_score": 1, "pages": 1})
    assert classify(doc("nic", "alfa"), t).document_type is None


def test_ocr_text_without_polish_letters_still_matches():
    t = types(a={"keywords": ["pełnomocnictwo przyjmuję"], "min_score": 1})
    assert classify(doc("Pelnomocnictwo przyjmuje:", source=PageSource.OCR), t).document_type == "a"


@pytest.mark.skipif(not TEMPLATE.exists(), reason="organizer data not mounted")
@pytest.mark.parametrize(
    ("filename", "expected"), [("negatywny przyklad.pdf", None), ("przyklad odwolanie.pdf", "odwolanie")]
)
def test_organizer_template_documents(filename, expected):
    shipped = load_document_types(ROOT / "config" / "document_types")
    # Classification looks at the first 2 pages only, so OCR of the rest of the scan is skipped.
    doc = read_pdf(TEMPLATE / filename, settings=Settings(ocr_max_pages=2))
    assert classify(doc, shipped).document_type == expected


TRAINING = sorted((DATA_DIR / "dane").glob("przyklad_*")) if (DATA_DIR / "dane").exists() else []


@pytest.mark.skipif(not TRAINING, reason="organizer data not mounted")
@pytest.mark.parametrize("case", TRAINING, ids=lambda p: p.name)
def test_training_documents_are_classified(case):
    shipped = load_document_types(ROOT / "config" / "document_types")
    for filename, expected in [
        ("odwolanie.pdf", "odwolanie"),
        ("pelnomocnictwo.pdf", "pelnomocnictwo"),
        ("potwierdzenie_przelewu.pdf", "przelew"),
    ]:
        pdf = transfer_pdf(case) if expected == "przelew" else case / filename
        assert classify(read_pdf(pdf), shipped).document_type == expected, filename
