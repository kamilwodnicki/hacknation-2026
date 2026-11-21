import json
import os
from pathlib import Path

import pytest
import yaml

from src.extraction import DocumentType, extract, load_document_types
from src.ingestion import IngestedDocument, Page, PageSource, read_pdf
from tests.conftest import transfer_pdf, without_account_prefix

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
TRAINING = sorted((DATA_DIR / "dane").glob("przyklad_*")) if (DATA_DIR / "dane").exists() else []


def doc(*pages: str) -> IngestedDocument:
    return IngestedDocument(
        filename="test.pdf",
        pages=[Page(number=i, text=t, source=PageSource.TEXT_LAYER) for i, t in enumerate(pages, start=1)],
    )


def doc_type(output: dict, **extra) -> DocumentType:
    return DocumentType.model_validate({"name": "t", "output": output, **extra})


def test_label_same_line_and_next_line():
    t = doc_type({"a": {"type": "date", "extract": [{"method": "label", "labels": ["Data operacji"]}]}})
    assert extract(doc("Data operacji: 10.03.2026"), t).data == {"a": "2026-03-10"}
    assert extract(doc("Data operacji\n2026-03-10"), t).data == {"a": "2026-03-10"}
    assert extract(doc("DATA OPERACJI ........ 10.03.2026"), t).data == {"a": "2026-03-10"}


def test_label_is_not_matched_in_lower_case_prose():
    t = doc_type({"a": {"type": "amount", "extract": [{"method": "label", "labels": ["Opłata"]}]}})
    assert extract(doc("opłata 50,00 skarbowa"), t).data == {"a": None}
    assert extract(doc("Opłata: 0,00 PLN"), t).data == {"a": 0.0}


def test_lookahead_stops_at_label_of_another_field():
    t = doc_type(
        {
            "z": {"type": "iban_pl", "extract": [{"method": "label", "labels": ["Nadawca"], "lookahead": 3}]},
            "na": {"type": "iban_pl", "extract": [{"method": "label", "labels": ["Odbiorca"], "lookahead": 3}]},
        }
    )
    text = "Nadawca\nFirma A\nOdbiorca\nFirma B\nPL61 1090 1014 0000 0712 1981 2874"
    assert extract(doc(text), t).data == {"z": None, "na": "PL61109010140000071219812874"}


def test_multiline_value_until_stop_label():
    t = doc_type(
        {"tytul": {"type": "text", "extract": [{"method": "label", "labels": ["Tytuł"], "multiline": True}]}},
        stop_labels=["Opłata", "Status"],
    )
    text = "Tytuł\nopłata skarbowa od\npełnomocnictwa ZP.1.2026\nStatus Wykonany"
    result = extract(doc(text), t)
    assert result.data == {"tytul": "opłata skarbowa od pełnomocnictwa ZP.1.2026"}
    assert result.fields["tytul"].page == 1


def test_regex_with_value_placeholder_spans_lines():
    t = doc_type(
        {"na": {"type": "iban_pl", "extract": [{"method": "regex", "pattern": r"na\s+rachunek\s+nr\s+({value})"}]}}
    )
    text = "wykonano przelew na rachunek nr PL61 1090 1014 0000 0712\n1981 2874, prowadzony dla X"
    assert extract(doc(text), t).data == {"na": "PL61109010140000071219812874"}


def test_nth_match_skips_duplicates():
    t = doc_type({"b": {"type": "date", "extract": [{"method": "nth_match", "n": 2}]}})
    assert extract(doc("2026-01-01 i 01.01.2026 oraz 2026-02-02"), t).data == {"b": "2026-02-02"}


def test_checksum_warn_and_reject():
    spec = {"type": "nip", "extract": [{"method": "label", "labels": ["NIP"]}]}
    warn = extract(doc("NIP: 5540240548"), doc_type({"nip": spec}))
    assert warn.data == {"nip": "5540240548"}
    assert "checksum" in warn.fields["nip"].warnings[0]
    reject = extract(doc("NIP: 5540240548"), doc_type({"nip": {**spec, "on_invalid_checksum": "reject"}}))
    assert reject.data == {"nip": None}


def test_nested_output_and_trace():
    t = doc_type({"x": {"y": {"type": "amount", "extract": [{"method": "label", "labels": ["Kwota"]}]}}})
    result = extract(doc("", "Kwota 1 500,00 zł"), t)
    assert result.data == {"x": {"y": 1500.0}}
    trace = result.fields["x.y"]
    assert (trace.page, trace.method, trace.raw) == (2, "rule", "1 500,00")


def test_invalid_config_is_rejected():
    with pytest.raises(ValueError, match="unknown type"):
        doc_type({"a": {"type": "nope"}})
    with pytest.raises(ValueError):
        doc_type({"a": {"type": "date", "extract": [{"method": "label"}]}})


def test_all_shipped_document_types_load():
    types = load_document_types(ROOT / "config" / "document_types")
    assert "przelew" in types
    reference = json.loads((ROOT / "tests" / "fixtures" / "przelew_keys.json").read_text(encoding="utf-8"))
    assert list(types["przelew"].fields()) == reference


def test_powody_dictionary_matches_training_data():
    powody = yaml.safe_load((ROOT / "config" / "dictionaries" / "czynnosc_powody.yaml").read_text(encoding="utf-8"))
    for case in TRAINING:
        ref = json.loads((case / "odwolanie.json").read_text(encoding="utf-8-sig"))["OdwolanieKIO"]
        assert powody[ref["czynnosc_powod_id"]] == ref["czynnosc_opis"]


@pytest.mark.skipif(not TRAINING, reason="organizer data not mounted")
@pytest.mark.parametrize("case", TRAINING, ids=lambda p: p.name)
def test_przelew_matches_reference(case):
    t = load_document_types(ROOT / "config" / "document_types")["przelew"]
    expected = json.loads((case / "przelew.json").read_text(encoding="utf-8-sig"))
    assert without_account_prefix(extract(read_pdf(transfer_pdf(case)), t).data) == expected
