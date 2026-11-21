"""The Streamlit results view renders real pipeline results without errors."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.pipeline import process_pdf

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
CASE = DATA_DIR / "dane" / "przyklad_42"
NEGATIVE = DATA_DIR / "szablon-aplikacja" / "input" / "case1" / "negatywny przyklad.pdf"


def test_ui_starts_without_results():
    at = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=30).run()
    assert not at.exception
    assert at.title[0].value == "Ekstrakcja danych z dokumentów KIO"


@pytest.mark.skipif(not CASE.exists() or not NEGATIVE.exists(), reason="organizer data not mounted")
def test_ui_renders_results_for_all_document_kinds():
    results = {}
    for pdf in [CASE / "odwolanie.pdf", CASE / "pelnomocnictwo.pdf", CASE / "potwierdzenie_przelewu.pdf", NEGATIVE]:
        results[pdf.name] = process_pdf(pdf, include_text=True).model_dump(mode="json")
    results["uszkodzony.pdf"] = {"filename": "uszkodzony.pdf", "error": "cannot open PDF", "output": {}, "document_type": None, "fields": {}}

    at = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=60)
    at.session_state["results"] = results
    at.run()

    assert not at.exception
    headers = [m.value for m in at.markdown if m.value.startswith("### ")]
    assert "### odwolanie.pdf — `odwolanie`" in headers
    assert "### negatywny przyklad.pdf — `nierozpoznany`" in headers
    assert any("cannot open PDF" in e.value for e in at.error)
    # summary table + per document: fields + classification tables (not for the broken file)
    assert len(at.dataframe) >= 1 + 2 * 4 - 1
