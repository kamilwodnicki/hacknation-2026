"""The Streamlit results view renders real pipeline results without errors (no API, no LLM)."""

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
    assert at.title[0].value == "PISMO — ekstrakcja danych z dokumentów KIO"


@pytest.mark.skipif(not CASE.exists() or not NEGATIVE.exists(), reason="organizer data not mounted")
def test_ui_renders_page_next_to_data_and_field_source():
    pdfs = [CASE / "odwolanie.pdf", CASE / "pelnomocnictwo.pdf", CASE / "potwierdzenie_przelewu.pdf", NEGATIVE]
    results = {pdf.name: process_pdf(pdf, include_text=True).model_dump(mode="json") for pdf in pdfs}
    files = {pdf.name: pdf.read_bytes() for pdf in pdfs}
    results["uszkodzony.pdf"] = {"filename": "uszkodzony.pdf", "error": "cannot open PDF", "output": {}, "document_type": None, "fields": {}}

    at = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=90)
    at.session_state["results"] = results
    at.session_state["files"] = files
    at.run()

    assert not at.exception
    headers = [m.value for m in at.markdown if m.value.startswith("### ")]
    assert "### odwolanie.pdf — `odwolanie`" in headers
    assert "### negatywny przyklad.pdf — `nierozpoznany`" in headers
    assert any("cannot open PDF" in e.value for e in at.error)
    assert len(at.get("image")) >= 4  # a rendered PDF page next to every readable document

    # Selecting a field shows its source (page, rule and fragment) next to the page.
    at.selectbox(key="field-potwierdzenie_przelewu.pdf").set_value("przelew_bankowy.kwota").run()
    assert not at.exception
    assert any("przelew_bankowy.kwota" in i.value and "strona 1" in i.value for i in at.info)

    # Hiding a document leaves only its header (name + type) with a button to show it again.
    images = len(at.get("image"))
    at.button(key="toggle-odwolanie.pdf").click().run()
    assert not at.exception
    assert "### odwolanie.pdf — `odwolanie`" in [m.value for m in at.markdown if m.value.startswith("### ")]
    assert not [s for s in at.selectbox if s.key == "field-odwolanie.pdf"]
    assert len(at.get("image")) == images - 1
    assert at.button(key="toggle-odwolanie.pdf").proto.icon == ":material/keyboard_arrow_down:"
    at.button(key="toggle-odwolanie.pdf").click().run()
    assert len(at.get("image")) == images
