"""List support in the extraction engine (type: list)."""

import pytest

from src.extraction import DocumentType, extract
from src.ingestion import IngestedDocument, Page, PageSource


def doc(text: str) -> IngestedDocument:
    return IngestedDocument(filename="t.pdf", pages=[Page(number=1, text=text, source=PageSource.TEXT_LAYER)])


def doc_type(output: dict, **extra) -> DocumentType:
    return DocumentType.model_validate({"name": "t", "output": output, **extra})


PARTY = {
    "nazwa": {"type": "text", "extract": [{"method": "nth_match", "n": 1}]},
    "krs": {"type": "krs", "extract": [{"method": "label", "labels": ["KRS"]}]},
    "nip": {"type": "nip", "checksum": "none", "extract": [{"method": "label", "labels": ["NIP"]}]},
}

APPEAL_HEADER = """Odwołujący:
Nordelia Facility Services S.A.
KRS: 9993307745, NIP: 9995519382
Zamawiający (zamawiający wspólnie przeprowadzający postępowanie):
1) Zamawiający – Lider, prowadzący postępowanie:
Małopolskie Centrum Logistyki Medycznej sp. z o.o.
KRS: 9991840562, NIP: 9998802341
2) Zamawiający – Partner:
Krakowskie Zakłady Komunalne S.A.
KRS: 9996035218, NIP: 9990457736
dotyczy: postępowania o udzielenie zamówienia"""


def appeal_type() -> DocumentType:
    return doc_type(
        {
            "Odwolujacy": {
                "type": "list",
                "split": {"method": "section", "start": ["Odwołujący"], "end": ["Zamawiający", "dotyczy"]},
                "item": PARTY,
            },
            "Zamawiajacy": {
                "type": "list",
                "split": {
                    "method": "section",
                    "start": ["Zamawiający"],
                    "end": ["Odwołujący", "dotyczy"],
                    "item_marker": r"^\s*\d+\)",
                },
                "item": {
                    "nazwa": {"type": "text", "extract": [{"method": "nth_match", "n": 2}]},
                    "krs": PARTY["krs"],
                },
            },
        }
    )


def test_section_split_single_item():
    data = extract(doc(APPEAL_HEADER), appeal_type()).data
    assert data["Odwolujacy"] == [{"nazwa": "Nordelia Facility Services S.A.", "krs": "9993307745", "nip": "9995519382"}]


def test_section_split_with_item_markers():
    result = extract(doc(APPEAL_HEADER), appeal_type())
    assert result.data["Zamawiajacy"] == [
        {"nazwa": "Małopolskie Centrum Logistyki Medycznej sp. z o.o.", "krs": "9991840562"},
        {"nazwa": "Krakowskie Zakłady Komunalne S.A.", "krs": "9996035218"},
    ]
    assert result.fields["Zamawiajacy[1].krs"].snippet == "KRS: 9996035218, NIP: 9990457736"


def test_section_without_markers_is_one_item():
    text = "Zamawiający:\nFilharmonia Pomorska\nKRS: 0000054588\ndotyczy: x"
    data = extract(doc(text), appeal_type()).data
    assert len(data["Zamawiajacy"]) == 1
    assert data["Zamawiajacy"][0]["krs"] == "0000054588"


def test_label_inside_enumeration():
    t = doc_type({"nip": {"type": "nip", "checksum": "none", "extract": [{"method": "label", "labels": ["NIP"]}]}})
    assert extract(doc("Meridian sp. j. (KRS 9998577437, NIP 9992049237), udzielam"), t).data == {"nip": "9992049237"}
    assert extract(doc("KRS 9998577437 · NIP 9992049237 · REGON 999851916"), t).data == {"nip": "9992049237"}
    assert extract(doc("bez etykiety 9992049237"), t).data == {"nip": None}


ATTORNEYS = {
    "pelnomocnicy": {
        "type": "list",
        "split": {
            "method": "matches",
            "pattern": r"(?:adw\.|r\.\s*pr\.)\s+(?P<imie_nazwisko>[A-ZŁŚŻ][a-ząćęłńóśźż]+\s+[A-ZŁŚŻ][a-ząćęłńóśźż]+)",
        },
        "unique_by": ["imie_nazwisko"],
        "item": {
            "imie_nazwisko": {"type": "text"},
            "pesel": {"type": "pesel", "extract": [{"method": "label", "labels": ["PESEL"]}]},
        },
    }
}


def test_matches_split_uses_named_groups_and_deduplicates():
    text = (
        "udzielam pełnomocnictwa adw. Patrycja Rutkiewicz (nr wpisu: WA 1), r. pr.\n"
        "Marek Łukaszewski (nr wpisu: WA 2).\nPełnomocnictwo przyjmuję: adw. Patrycja Rutkiewicz"
    )
    result = extract(doc(text), doc_type(ATTORNEYS))
    assert result.data == {
        "pelnomocnicy": [
            {"imie_nazwisko": "Patrycja Rutkiewicz", "pesel": None},
            {"imie_nazwisko": "Marek Łukaszewski", "pesel": None},
        ]
    }
    assert result.fields["pelnomocnicy[1].imie_nazwisko"].rule == "pattern match"
    assert "pelnomocnicy[2].imie_nazwisko" not in result.fields  # dropped duplicate leaves no trace


def test_nested_list_with_document_scope():
    output = {
        "mocodawca": {
            "type": "list",
            # "Mocodawca Centaur ..." — label followed by the value, not a heading
            "split": {"method": "section", "start": ["Mocodawca"], "end": ["Pełnomocnik"], "heading_only": False},
            "max_items": 1,
            "item": {
                "data": {"krs": PARTY["krs"]},
                "podpisujacy": {
                    "type": "list",
                    "scope": "document",
                    "split": {"method": "matches", "pattern": r"\.{5,}\n(?P<imie_nazwisko>[^\n]+)"},
                    "item": {"imie_nazwisko": {"type": "text"}},
                },
            },
        }
    }
    text = "Mocodawca Centaur sp. z o.o.\nKRS 9996203344\nPełnomocnik adw. X Y\n......\nIgnacy Siedlecki\nCzłonek Zarządu\n......\nNorbert Głowacz"
    data = extract(doc(text), doc_type(output)).data
    assert data == {
        "mocodawca": [
            {
                "data": {"krs": "9996203344"},
                "podpisujacy": [{"imie_nazwisko": "Ignacy Siedlecki"}, {"imie_nazwisko": "Norbert Głowacz"}],
            }
        ]
    }


def test_empty_items_are_dropped_and_max_items_applies():
    t = doc_type(
        {
            "l": {
                "type": "list",
                "max_items": 2,
                "split": {"method": "matches", "pattern": r"#(?P<v>\w*)"},
                "item": {"v": {"type": "reference"}},
            }
        }
    )
    assert extract(doc("#A1B2C3 # #D4E5F6 #G7H8I9"), t).data == {"l": [{"v": "A1B2C3"}, {"v": "D4E5F6"}]}


def test_list_without_split_is_empty_until_llm():
    t = doc_type({"l": {"type": "list", "description": "filled by LLM", "item": {"a": {"type": "text"}}}})
    assert extract(doc("anything"), t).data == {"l": []}


def test_fields_lists_item_paths():
    assert list(appeal_type().fields())[:3] == ["Odwolujacy[].nazwa", "Odwolujacy[].krs", "Odwolujacy[].nip"]


def test_invalid_list_config():
    with pytest.raises(ValueError):
        doc_type({"l": {"type": "list", "item": {"a": {"type": "text"}}, "split": {"method": "matches", "pattern": "("}}})
    with pytest.raises(ValueError):
        doc_type({"l": {"type": "list"}})
