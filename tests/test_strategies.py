"""Strategies and value types added for appeals and powers of attorney."""

import json
import os
from pathlib import Path

import pytest

from src.extraction import DocumentType, extract, load_document_types
from src.ingestion import IngestedDocument, Page, PageSource, read_pdf
from src.validation.normalizers import VALUE_TYPES, expand_placeholders

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
TRAINING = sorted((DATA_DIR / "dane").glob("przyklad_*")) if (DATA_DIR / "dane").exists() else []


def doc(*pages: str) -> IngestedDocument:
    return IngestedDocument(
        filename="t.pdf",
        pages=[Page(number=i, text=t, source=PageSource.TEXT_LAYER) for i, t in enumerate(pages, start=1)],
    )


def doc_type(output: dict) -> DocumentType:
    return DocumentType.model_validate({"name": "t", "output": output})


def test_placeholders_expand_only_known_types():
    assert expand_placeholders("x{2,5}", None) == "x{2,5}"
    assert VALUE_TYPES["date"].pattern in expand_placeholders("w dniu {date}", None)
    assert VALUE_TYPES["nip"].pattern in expand_placeholders("({value})", "nip")


@pytest.mark.parametrize(
    ("value_type", "text", "expected"),
    [
        ("person", "adw. Natalia Górecka (nr wpisu)", "Natalia Górecka"),
        ("person", "r. pr. Anna Nowak-Kowalska", "Anna Nowak-Kowalska"),
        ("company", "Mocodawcą jest Zarendel Automatyka sp. j., ul. Sosnowa", "Mocodawcą jest Zarendel Automatyka sp. j."),
        ("company", "Hartica Serwis S.A.", "Hartica Serwis S.A."),
        ("email", "tel. 000, e-mail: Biuro@Kancelaria.example.", "biuro@kancelaria.example"),
        ("place", "Zielona Góra, 7 marca 2026", "Zielona Góra"),
        ("integer", "nr 12", 12),
    ],
)
def test_new_value_types(value_type, text, expected):
    import re

    vt = VALUE_TYPES[value_type]
    m = re.search(vt.pattern, text, re.IGNORECASE)
    assert m and vt.normalize(m.group(0)) == expected


def test_person_is_case_sensitive_even_when_search_ignores_case():
    import re

    assert re.search(VALUE_TYPES["person"].pattern, "ala ma kota", re.IGNORECASE) is None


def test_regex_group_and_pages():
    t = doc_type(
        {
            "miejscowosc": {
                "type": "place",
                "extract": [{"method": "regex", "pages": 1, "flags": ["MULTILINE"], "pattern": r"^({place}),\s+{date}"}],
            },
            "data": {
                "type": "date",
                "extract": [
                    {"method": "regex", "pages": 1, "group": "d", "flags": ["MULTILINE"], "pattern": r"^{place},\s+(?P<d>{date})"}
                ],
            },
        }
    )
    assert extract(doc("Kraków, 02.07.2026\nTreść"), t).data == {"miejscowosc": "Kraków", "data": "2026-07-02"}
    assert extract(doc("Treść", "Kraków, 02.07.2026"), t).data == {"miejscowosc": None, "data": None}


def test_label_until_cuts_text_value():
    t = doc_type(
        {"n": {"type": "text", "extract": [{"method": "label", "labels": ["adres"], "multiline": True, "until": r",\s*ul\."}]}}
    )
    text = "adres: Kancelaria Adwokacka Spółka z ograniczoną\nodpowiedzialnością, ul. Jasionowa 19"
    assert extract(doc(text), t).data == {"n": "Kancelaria Adwokacka Spółka z ograniczoną odpowiedzialnością"}


def test_keyword_map_order_within_and_default():
    spec = {
        "type": "integer",
        "extract": [
            {
                "method": "keyword_map",
                "within": r"Zamawiający\s+w\s+dniu\s+{date}\s*(?:roku)?\s*([^.]*)",
                "map": [{"value": 7, "any": ["nie odrzucił"]}, {"value": 1, "any": ["odrzucił"]}],
                "default": 0,
            }
        ],
    }
    t = doc_type({"id": spec})
    assert extract(doc("Zamawiający w dniu 20 marca 2026 roku nie odrzucił oferty."), t).data == {"id": 7}
    assert extract(doc("Zamawiający w dniu 20 marca 2026 roku ODRZUCIŁ ofertę."), t).data == {"id": 1}
    assert extract(doc("Inny tekst, odrzucił."), t).data == {"id": 0}  # keyword outside `within`


def test_derived_and_lookup_use_sibling_values():
    t = DocumentType.model_validate(
        {
            "name": "t",
            "output": {
                "id": {"type": "integer", "extract": [{"method": "regex", "pattern": r"powód (\d+)"}]},
                "opis": {"type": "text", "extract": [{"method": "lookup", "from": "id", "dictionary": "czynnosc_powody"}]},
                "ma_id": {"type": "integer", "extract": [{"method": "derived", "from": "id", "if_present": 1, "if_absent": 0}]},
            },
        }
    )
    t.load_dictionaries(ROOT / "config" / "dictionaries")
    assert extract(doc("powód 9"), t).data == {"id": 9, "opis": "Decyzja o unieważnieniu postępowania", "ma_id": 1}
    result = extract(doc("brak"), t)
    assert result.data == {"id": None, "opis": None, "ma_id": 0}
    assert result.fields["ma_id"].rule == "#1 derived from id"


def test_missing_dictionary_fails_at_load(tmp_path):
    t = doc_type({"o": {"type": "text", "extract": [{"method": "lookup", "from": "x", "dictionary": "nope"}]}})
    with pytest.raises(ValueError, match="dictionary 'nope' not found"):
        t.load_dictionaries(tmp_path)


def test_split_alternatives_and_derived_only_items_are_dropped():
    t = doc_type(
        {
            "l": {
                "type": "list",
                "split": [
                    {"method": "matches", "pattern": r"\d\)\s*(?P<n>{company})", "min_items": 2},
                    {"method": "whole"},
                ],
                "item": {
                    "n": {"type": "company", "extract": [{"method": "nth_match", "n": 1}]},
                    "flag": {"type": "integer", "extract": [{"method": "derived", "from": "n", "if_present": 1, "if_absent": 0}]},
                },
            }
        }
    )
    assert extract(doc("1) Alfa sp. z o.o.; 2) Beta S.A."), t).data == {"l": [{"n": "Alfa sp. z o.o.", "flag": 1}, {"n": "Beta S.A.", "flag": 1}]}
    assert extract(doc("Wykonawca: Gamma sp. j."), t).data == {"l": [{"n": "Gamma sp. j.", "flag": 1}]}
    assert extract(doc("nic tu nie ma"), t).data == {"l": []}  # only the derived 0 -> item dropped


def test_heading_only_sections():
    t = doc_type(
        {
            "z": {
                "type": "list",
                "split": {"method": "section", "start": ["Zamawiający"], "end": ["Koniec"]},
                "item": {"nip": {"type": "nip", "checksum": "none", "extract": [{"method": "label", "labels": ["NIP"]}]}},
            }
        }
    )
    text = "Zamawiający w dniu 1 marca 2026 r. NIP: 1111111111\nZamawiający:\nNIP: 2222222222\nKoniec"
    assert extract(doc(text), t).data == {"z": [{"nip": "2222222222"}]}


@pytest.mark.skipif(not TRAINING, reason="organizer data not mounted")
@pytest.mark.parametrize("kind", ["odwolanie", "pelnomocnictwo"])
def test_training_f1_does_not_regress(kind):
    """Guards the current rule quality on the training set (update when it improves)."""
    from src.evaluation.metrics import Counts, compare

    t = load_document_types(ROOT / "config" / "document_types")[kind]
    total = Counts()
    for case in TRAINING:
        reference = json.loads((case / f"{kind}.json").read_text(encoding="utf-8-sig"))
        for counts in compare(extract(read_pdf(case / f"{kind}.pdf"), t).data, reference).strict.values():
            total += counts
    assert total.f1 >= {"odwolanie": 0.995, "pelnomocnictwo": 0.995}[kind]
