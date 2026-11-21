import os
from pathlib import Path

import pytest

from src.config import Settings
from src.ingestion import IngestionError, PageSource, read_pdf
from src.ingestion.ocr import OcrBox, group_into_lines
from src.ingestion.pdf_reader import clean_text, has_usable_text
from tests.conftest import transfer_pdf

# Organizer repository mounted read-only (see docker-compose.yml, UZP_DATA_DIR)
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
TRAINING = DATA_DIR / "dane" / "przyklad_01"
SCAN = DATA_DIR / "szablon-aplikacja" / "input" / "case1" / "przyklad odwolanie.pdf"
needs_data = pytest.mark.skipif(not TRAINING.exists(), reason="organizer data not mounted")


def box(text, x0, x1, y0, y1):
    return OcrBox(text, 0.9, x0, x1, y0, y1)


def test_group_into_lines_orders_by_row_then_column():
    boxes = [
        box("Rachunek", 600, 760, 102, 122),
        box("Płatnik", 10, 120, 100, 120),
        box("Belmoria", 10, 150, 140, 160),
        box("S.A.", 158, 200, 141, 161),
    ]
    assert group_into_lines(boxes) == "Płatnik    Rachunek\nBelmoria S.A."


def test_group_into_lines_empty():
    assert group_into_lines([]) == ""


def test_clean_text_normalizes_unicode_and_newlines():
    decomposed = "Odwołujący  \r\nx\x00"  # "ą" as a + combining ogonek
    assert clean_text(decomposed) == "Odwołujący\nx"


def test_has_usable_text():
    assert not has_usable_text("  \n -- 1 -- \n", 30)
    assert has_usable_text("Krajowa Izba Odwoławcza w Warszawie", 30)


def test_not_a_pdf_raises(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    with pytest.raises(IngestionError):
        read_pdf(bad)


@needs_data
def test_digital_pdf_uses_text_layer():
    doc = read_pdf(TRAINING / "odwolanie.pdf")
    assert doc.ocr_pages == []
    assert all(p.source == PageSource.TEXT_LAYER for p in doc.pages)
    text = doc.full_text()
    assert "Odwołujący" in text and "9999405188" in text


@needs_data
def test_bytes_input_matches_path_input():
    path = transfer_pdf(TRAINING)
    assert read_pdf(path.read_bytes(), filename=path.name).full_text() == read_pdf(path).full_text()


@needs_data
@pytest.mark.skipif(not SCAN.exists(), reason="scan sample not mounted")
def test_ocr_cache_returns_same_text_without_ocr(tmp_path, monkeypatch):
    settings = Settings(ocr_max_pages=1, ocr_cache_dir=tmp_path)
    first = read_pdf(SCAN, settings=settings)
    assert list(tmp_path.rglob("*_p1_dpi200_det-tiny.json"))

    import src.ingestion.pdf_reader as reader

    monkeypatch.setattr(reader, "ocr_image", lambda *a, **k: pytest.fail("OCR should come from the cache"))
    assert read_pdf(SCAN, settings=settings).full_text() == first.full_text()


@needs_data
@pytest.mark.skipif(not SCAN.exists(), reason="scan sample not mounted")
def test_scanned_pdf_falls_back_to_ocr():
    doc = read_pdf(SCAN, settings=Settings(ocr_max_pages=1))
    assert doc.ocr_pages == [1]
    assert doc.skipped_pages == list(range(2, doc.page_count + 1))
    assert "Krajowej Izby" in doc.pages[0].text
    assert doc.pages[0].ocr_confidence > 0.8
