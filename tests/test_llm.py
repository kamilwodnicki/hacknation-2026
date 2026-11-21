"""LLM integration tested with a fake model — no paid API calls."""

import json
from pathlib import Path

import pytest

from src import pipeline
from src.extraction import DocumentType, extract, load_document_types
from src.ingestion import IngestedDocument, Page, PageSource
from src.llm.cache import USAGE, CachedLLM
from src.llm.client import ChatResponse, LLMError
from src.llm.extractor import build_messages, has_gaps, merge, parse_json

ROOT = Path(__file__).resolve().parents[1]


class FakeLLM:
    description = "fake"
    model = "fake-model"

    def __init__(self, answer: dict | str | Exception):
        self.answer = answer
        self.calls: list[list[dict]] = []

    def chat(self, messages, max_tokens=1024, temperature=0.0, json_mode=False):
        self.calls.append(messages)
        if isinstance(self.answer, Exception):
            raise self.answer
        text = self.answer if isinstance(self.answer, str) else json.dumps(self.answer, ensure_ascii=False)
        return ChatResponse(text=text, model=self.model, input_tokens=100, output_tokens=20)


def doc(text: str) -> IngestedDocument:
    return IngestedDocument(filename="t.pdf", pages=[Page(number=1, text=text, source=PageSource.TEXT_LAYER)])


def doc_type(output: dict, **extra) -> DocumentType:
    t = DocumentType.model_validate({"name": "t", "description": "test", "output": output, **extra})
    t.load_dictionaries(ROOT / "config" / "dictionaries")
    return t


TEXT = "Pełnomocnictwo dla Janowi Kowalskiemu.\nNIP: 5540240549\nKwota 100,00 zł"
TYPE = {
    "nip": {"type": "nip", "description": "NIP mocodawcy", "extract": [{"method": "label", "labels": ["NIP"]}]},
    "osoba": {"type": "person", "description": "pełnomocnik"},
    "kwota": {"type": "amount", "extract": [{"method": "label", "labels": ["Kwota"]}]},
}


def test_prompt_contains_schema_skeleton_and_text():
    t = doc_type(TYPE)
    messages = build_messages(doc(TEXT), t, max_chars=10_000)
    user = messages[1]["content"]
    assert "- nip: NIP: 10 cyfr bez kresek — NIP mocodawcy" in user
    assert '"osoba": null' in user
    assert "Janowi Kowalskiemu" in user


def test_prompt_insists_on_nominative_names():
    t = doc_type(TYPE)
    system, user = (m["content"] for m in build_messages(doc(TEXT), t, 10_000))
    assert "'Leszkowi Wieczorkowi' -> 'Leszek Wieczorek'" in system
    assert "- osoba: imię i nazwisko w MIANOWNIKU" in user
    assert user.rstrip().endswith("nie 'Grzegorzowi Wiśniewskiemu').")  # reminder after the document


def test_prompt_lists_dictionary_values_for_lookup_source():
    t = load_document_types(ROOT / "config" / "document_types")["odwolanie"]
    user = build_messages(doc("x"), t, 1000)[1]["content"]
    assert "12 = Projektowane postanowienia umowy" in user
    assert "czynnosc_opis" not in user.split("Szablon JSON")[0]  # computed field not asked for


def test_prompt_text_is_truncated():
    user = build_messages(doc("a" * 5000), doc_type(TYPE), max_chars=100)[1]["content"]
    assert "dalsza część dokumentu pominięta" in user


def test_parse_json_accepts_code_fences_and_rejects_garbage():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('Oto wynik: {"a": 2} koniec') == {"a": 2}
    with pytest.raises(LLMError):
        parse_json("brak")


def test_merge_fills_only_gaps_and_grounds_values():
    t = doc_type(TYPE)
    d = doc(TEXT)
    rules = extract(d, t)
    assert rules.data == {"nip": "5540240549", "osoba": None, "kwota": 100.0}
    merged = merge(rules, {"nip": "1111111111", "osoba": "Jan Kowalski", "kwota": 100}, d, t, "fake")
    assert merged.data == {"nip": "5540240549", "osoba": "Jan Kowalski", "kwota": 100.0}
    assert merged.fields["osoba"].method == "llm"
    assert merged.fields["kwota"].method == "rule+llm"
    assert any("1111111111" in w for w in merged.fields["nip"].warnings)


def test_invented_value_is_rejected():
    t = doc_type(TYPE)
    d = doc("Kwota 100,00 zł.")
    merged = merge(extract(d, t), {"nip": "5540240549", "osoba": "Adam Nowak"}, d, t, "fake")
    assert merged.data["nip"] is None and merged.data["osoba"] is None


def test_prefer_and_never_policies():
    t = doc_type(
        {
            "a": {"type": "text", "llm": "prefer", "extract": [{"method": "label", "labels": ["A"]}]},
            "b": {"type": "text", "llm": "never"},
        }
    )
    d = doc("A: stara wartość\nnowa wartość i inne")
    merged = merge(extract(d, t), {"a": "nowa wartość", "b": "inne"}, d, t, "fake")
    assert merged.data == {"a": "nowa wartość", "b": None}
    assert "reguła: stara wartość" in merged.fields["a"].warnings


def test_prefer_does_not_replace_rule_with_its_own_fragment():
    t = doc_type({"a": {"type": "text", "llm": "prefer", "extract": [{"method": "label", "labels": ["Tytuł"]}]}})
    d = doc("Tytuł: wpis od odwołania ZP.1.2026 CEN123456")
    merged = merge(extract(d, t), {"a": "wpis od odwołania ZP.1.2026"}, d, t, "fake")
    assert merged.data == {"a": "wpis od odwołania ZP.1.2026 CEN123456"}
    assert any("fragment" in w for w in merged.fields["a"].warnings)


def test_lists_from_model_when_rules_found_none_and_pairing_by_key():
    t = doc_type(
        {
            "osoby": {
                "type": "list",
                "unique_by": ["imie"],
                "split": {"method": "matches", "pattern": r"adw\.\s+(?P<imie>{person})"},
                "item": {"imie": {"type": "person"}, "pesel": {"type": "pesel", "checksum": "none"}},
            }
        }
    )
    d = doc("adw. Anna Nowak oraz radca Piotr Zieliński, PESEL 44051401359")
    rules = extract(d, t)
    assert rules.data == {"osoby": [{"imie": "Anna Nowak", "pesel": None}]}
    llm = {"osoby": [{"imie": "Piotr Zieliński", "pesel": "44051401359"}, {"imie": "Anna Nowak", "pesel": None}]}
    # Rules found a list -> the paired item (matched by name) is filled; an extra model item is
    # added only because it carries an identifier (PESEL) found in the document.
    assert merge(rules, llm, d, t, "fake").data == {
        "osoby": [{"imie": "Anna Nowak", "pesel": None}, {"imie": "Piotr Zieliński", "pesel": "44051401359"}]
    }
    # Without an identifier (or with an invented one) the extra item is not added.
    no_id = {"osoby": [{"imie": "Piotr Zieliński", "pesel": "90010112345"}, {"imie": "Anna Nowak", "pesel": None}]}
    assert merge(rules, no_id, d, t, "fake").data == {"osoby": [{"imie": "Anna Nowak", "pesel": None}]}
    # Rules found nothing -> the model's list is used (validated item by item).
    d2 = doc("radca Piotr Zieliński, PESEL 44051401359")
    assert merge(extract(d2, t), llm, d2, t, "fake").data == {
        "osoby": [{"imie": "Piotr Zieliński", "pesel": "44051401359"}]
    }


def test_list_items_paired_by_registry_id_when_rule_name_is_wrong():
    t = doc_type(
        {
            "firmy": {
                "type": "list",
                "unique_by": ["nazwa"],
                "split": {"method": "whole"},
                "item": {
                    "nazwa": {"type": "company", "extract": [{"method": "nth_match", "n": 1}]},
                    "nip": {"type": "nip", "checksum": "none", "extract": [{"method": "nth_match", "n": 1}]},
                    "osoby": {
                        "type": "list",
                        "scope": "document",
                        "split": {"method": "matches", "pattern": r"Podpis:\s*(?P<imie>{person})"},
                        "item": {"imie": {"type": "person"}},
                    },
                },
            }
        }
    )
    # The letterhead (a law firm) is taken by the rule as the company name.
    d = doc("Lex Kancelaria sp. k.\nAlfa Budowa S.A. z siedzibą w Opolu, NIP 1234567890\nJan Nowak")
    rules = extract(d, t)
    assert rules.data["firmy"][0]["nazwa"] == "Lex Kancelaria sp. k."
    llm = {"firmy": [{"nazwa": "Alfa Budowa S.A.", "nip": "1234567890", "osoby": [{"imie": "Jan Nowak"}]}]}
    merged = merge(rules, llm, d, t, "fake").data["firmy"]
    # Same NIP -> same item: the model's people are kept (rule name stays, policy "fill").
    assert merged == [{"nazwa": "Lex Kancelaria sp. k.", "nip": "1234567890", "osoby": [{"imie": "Jan Nowak"}]}]


def test_derived_and_lookup_fields_are_recomputed_after_merge():
    t = doc_type(
        {
            "id": {"type": "integer"},
            "opis": {"type": "text", "extract": [{"method": "lookup", "from": "id", "dictionary": "czynnosc_powody"}]},
        }
    )
    d = doc("Zamawiający zaniechał wykluczenia — powód 8")
    merged = merge(extract(d, t), {"id": 8, "opis": "zmyślony opis"}, d, t, "fake")
    assert merged.data == {"id": 8, "opis": "Zaniechanie wykluczenia wykonawcy"}


def test_has_gaps():
    t = doc_type(TYPE)
    assert has_gaps(extract(doc(TEXT), t), t)  # osoba missing
    assert not has_gaps(extract(doc(TEXT), doc_type({"nip": TYPE["nip"]})), doc_type({"nip": TYPE["nip"]}))


def test_cache_pays_once(tmp_path):
    fake = FakeLLM({"a": 1})
    cached = CachedLLM(fake, tmp_path)
    before = (USAGE.api_calls, USAGE.cache_hits)
    first = cached.chat([{"role": "user", "content": "x"}], json_mode=True)
    second = cached.chat([{"role": "user", "content": "x"}], json_mode=True)
    assert len(fake.calls) == 1
    assert not first.cached and second.cached and second.text == first.text
    assert (USAGE.api_calls - before[0], USAGE.cache_hits - before[1]) == (1, 1)


@pytest.fixture
def fake_llm(monkeypatch):
    def install(answer):
        fake = FakeLLM(answer)
        monkeypatch.setattr(pipeline, "_llm_client", fake)
        return fake

    return install


def test_pipeline_hybrid_uses_model_only_when_rules_have_gaps(fake_llm):
    t = doc_type(TYPE)
    fake = fake_llm({"osoba": "Jan Kowalski"})
    result, info = pipeline.extract_with_llm(doc(TEXT), t, mode="hybrid")
    assert info.used and result.data["osoba"] == "Jan Kowalski"
    complete = doc_type({"nip": TYPE["nip"]})
    _, info = pipeline.extract_with_llm(doc(TEXT), complete, mode="hybrid")
    assert not info.used and info.skipped_reason
    assert len(fake.calls) == 1


def test_prefer_field_is_sent_to_model_even_when_rules_are_complete(fake_llm):
    t = doc_type({"nip": {**TYPE["nip"], "llm": "prefer"}})
    fake = fake_llm({"nip": "5540240549"})
    _, info = pipeline.extract_with_llm(doc(TEXT), t, mode="hybrid")
    assert info.used and len(fake.calls) == 1


def test_rules_list_items_are_not_duplicated_by_model_variants():
    t = doc_type(
        {
            "osoby": {
                "type": "list",
                "unique_by": ["imie"],
                "split": {"method": "matches", "pattern": r"adw\.\s+(?P<imie>{person})"},
                "item": {"imie": {"type": "person"}},
            }
        }
    )
    d = doc("pełnomocnictwa adw. Grzegorz Wiśniewski")
    merged = merge(extract(d, t), {"osoby": [{"imie": "Grzegorz Wiśniewski"}, {"imie": "Grzegorzowi Wiśniewskiemu"}]}, d, t, "f")
    assert merged.data == {"osoby": [{"imie": "Grzegorz Wiśniewski"}]}


def test_model_turns_declined_rule_name_into_nominative():
    t = doc_type(
        {
            "osoby": {
                "type": "list",
                "unique_by": ["imie"],
                "split": {"method": "matches", "pattern": r"pełnomocnictwa\s+(?P<imie>{person})"},
                "item": {"imie": {"type": "person", "llm": "prefer"}},
            }
        }
    )
    d = doc("udzielam pełnomocnictwa Leszkowi Wieczorkowi")
    rules = extract(d, t)
    assert rules.data == {"osoby": [{"imie": "Leszkowi Wieczorkowi"}]}  # rules keep the document form
    merged = merge(rules, {"osoby": [{"imie": "Leszek Wieczorek"}]}, d, t, "f")
    assert merged.data == {"osoby": [{"imie": "Leszek Wieczorek"}]}
    assert merged.fields["osoby[0].imie"].method == "llm"
    assert "reguła: Leszkowi Wieczorkowi" in merged.fields["osoby[0].imie"].warnings


ARB_TYPE = {
    "id": {
        "type": "integer",
        "llm": "arbitrate",
        "llm_evidence": True,
        "extract": [{"method": "regex", "pattern": r"powód (\d+)"}],
    }
}


def test_evidence_key_is_requested_before_the_field():
    user = build_messages(doc("x"), doc_type(ARB_TYPE), 1000)[1]["content"]
    assert user.index('"id_cytat"') < user.index('"id"')
    assert "- id_cytat: najpierw przepisz dosłownie zdanie" in user


@pytest.mark.parametrize(("choice", "expected"), [("B", 8), ("A", 3)])
def test_arbitrate_asks_second_call_on_disagreement(choice, expected):
    t = doc_type(ARB_TYPE)
    d = doc("powód 3\nZamawiający nie wykluczył wykonawcy")
    arbiter = FakeLLM({"wybor": choice})
    merged = merge(extract(d, t), {"id_cytat": "Zamawiający nie wykluczył wykonawcy", "id": 8}, d, t, "f", arbiter=arbiter)
    assert merged.data == {"id": expected}
    assert len(arbiter.calls) == 1
    assert "Kandydat B: 8" in arbiter.calls[0][1]["content"]
    assert "id_cytat" not in merged.data


def test_trusted_strategy_is_not_arbitrated_but_weaker_one_is():
    trusted = {
        "id": {
            **ARB_TYPE["id"],
            "extract": [
                {"method": "regex", "pattern": r"zarzut (\d+)", "trusted": True},
                {"method": "regex", "pattern": r"powód (\d+)"},
            ],
        }
    }
    t = doc_type(trusted)
    arbiter = FakeLLM({"wybor": "B"})
    d = doc("zarzut 4\npowód 3")
    merged = merge(extract(d, t), {"id": 8}, d, t, "f", arbiter=arbiter)
    assert merged.data == {"id": 4} and arbiter.calls == []
    assert any("trusted" in w for w in merged.fields["id"].warnings)
    d2 = doc("powód 3")  # only the weaker strategy matched -> arbitration as usual
    assert merge(extract(d2, t), {"id": 8}, d2, t, "f", arbiter=arbiter).data == {"id": 8}
    assert len(arbiter.calls) == 1


def test_arbitrate_without_arbiter_keeps_rule_and_agreement_needs_no_call():
    t = doc_type(ARB_TYPE)
    d = doc("powód 3")
    assert merge(extract(d, t), {"id": 8}, d, t, "f").data == {"id": 3}
    arbiter = FakeLLM({"wybor": "B"})
    assert merge(extract(d, t), {"id": 3}, d, t, "f", arbiter=arbiter).data == {"id": 3}
    assert arbiter.calls == []


def test_name_gate_keeps_nominative_rule_value_and_rejects_two_people():
    t = doc_type({"p": {"type": "person", "llm": "prefer", "extract": [{"method": "label", "labels": ["Pełnomocnik"]}]}})
    d = doc("Pełnomocnik: Dorota Zawadzki\noraz Michał Borkowski")
    assert merge(extract(d, t), {"p": "Dorota Zawadzka"}, d, t, "f").data == {"p": "Dorota Zawadzki"}
    t2 = doc_type({"p": {"type": "person"}})
    assert merge(extract(d, t2), {"p": "Dorota Zawadzki, Michał Borkowski"}, d, t2, "f").data == {"p": None}


def test_pipeline_llm_mode_ignores_rules(fake_llm):
    t = doc_type(TYPE)
    fake_llm({"nip": "5540240549", "osoba": None, "kwota": None})
    result, info = pipeline.extract_with_llm(doc(TEXT), t, mode="llm")
    assert result.data == {"nip": "5540240549", "osoba": None, "kwota": None}


def test_pipeline_falls_back_to_rules_when_model_fails(fake_llm):
    t = doc_type(TYPE)
    fake_llm(LLMError("timeout"))
    result, info = pipeline.extract_with_llm(doc(TEXT), t, mode="hybrid")
    assert result.data["nip"] == "5540240549" and info.error == "timeout" and not info.used


def test_rules_mode_without_provider_never_calls_model(fake_llm):
    fake = fake_llm({"osoba": "Jan Kowalski"})
    pipeline.extract_with_llm(doc(TEXT), doc_type(TYPE), mode="rules")
    assert fake.calls == []


def test_account_prefix_follows_the_document_not_the_model():
    t = doc_type({"z": {"type": "iban_pl", "llm": "prefer"}, "na": {"type": "iban_pl", "llm": "prefer"}})
    d = doc("Z rachunku PL61 1090 1014 0000 0712 1981 2874\nNa rachunek 60 1010 1010 0081 3622 3100 0000")
    llm = {"z": "61109010140000071219812874", "na": "PL60101010100081362231000000"}
    assert merge(extract(d, t), llm, d, t, "fake").data == {
        "z": "PL61109010140000071219812874",
        "na": "60101010100081362231000000",
    }
