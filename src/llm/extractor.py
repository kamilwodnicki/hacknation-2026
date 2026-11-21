"""LLM extraction driven by the same YAML document types as the rules.

1. The prompt is built from the output template: the JSON skeleton to fill, every field's
   type and `description`, and allowed values of dictionary-backed fields.
2. The answer is validated field by field with the same guards as rule values
   (normalization, must_match / reject, checksums) plus *grounding*: the value must be
   present in the document text — a value the model invented is rejected.
3. Merge with the rule result according to each field's `llm` policy (fill / prefer / never);
   derived and lookup fields are recomputed afterwards.
"""

import json
import re
from typing import Any

from src.extraction.engine import ExtractionResult, FieldTrace, apply_dependents
from src.extraction.schema import DocumentType, FieldSpec, ListSpec, LookupStrategy
from src.ingestion import IngestedDocument
from src.llm.client import ChatResponse, LLMClient, LLMError
from src.validation.checksums import CHECKSUMS
from src.validation.normalizers import VALUE_TYPES, fold

TYPE_HINTS = {
    "date": "data w formacie RRRR-MM-DD",
    "amount": "liczba (np. 10000.00)",
    "iban_pl": "numer rachunku: 26 cyfr bez spacji i bez PL",
    "nip": "NIP: 10 cyfr bez kresek",
    "regon": "REGON: 9 lub 14 cyfr",
    "krs": "KRS: 10 cyfr",
    "pesel": "PESEL: 11 cyfr (jako tekst)",
    "ted": "numer TED w formacie NNNNNN-RRRR",
    "bzp": "numer BZP w formacie RRRR/BZP NNNNNNNN bez spacji",
    "reference": "identyfikator przepisany dokładnie z dokumentu",
    "text": "tekst przepisany z dokumentu",
    "integer": "liczba całkowita",
    "email": "adres e-mail",
    "person": "imię i nazwisko w MIANOWNIKU (kto?), np. 'Jan Kowalski', nie 'Janowi Kowalskiemu'",
    "company": "pełna nazwa podmiotu z formą prawną",
    "place": "nazwa miejscowości w mianowniku",
}

SYSTEM_PROMPT = (
    "Jesteś systemem ekstrakcji danych z polskich dokumentów postępowań odwoławczych przed "
    "Krajową Izbą Odwoławczą. Zwracasz WYŁĄCZNIE jeden obiekt JSON o dokładnie takiej strukturze "
    "jak podany szablon (te same klucze, bez dodatkowych pól). Zasady:\n"
    "- wartości bierz wyłącznie z treści dokumentu; jeśli informacji nie ma — wpisz null, nigdy nie zgaduj;\n"
    "- daty w formacie RRRR-MM-DD; NIP, REGON, KRS, PESEL i numery rachunków jako same cyfry;\n"
    "- imiona i nazwiska przepisuj DOKŁADNIE tak, jak w dokumencie — nie zmieniaj płci, pisowni ani "
    "formy nazwiska (np. 'Dorota Zawadzki' zostaje 'Dorota Zawadzki', 'Aleksandra' zostaje 'Aleksandra'); "
    "zmieniaj wyłącznie przypadek na mianownik (kto?), gdy w dokumencie stoi inny przypadek — patrz przykłady niżej;\n"
    "- jedno pole osoby = jedna osoba; gdy osób jest kilka, a pole nie jest listą, podaj pierwszą;\n"
    "- listy: podaj wszystkie elementy występujące w dokumencie; pusta lista, jeśli brak;\n"
    "- pola liczbowe jako liczby JSON, pozostałe jako tekst.\n\n"
    "Przykłady zamiany imion i nazwisk na mianownik (tekst w dokumencie -> wartość w JSON):\n"
    "- 'udzielam pełnomocnictwa Janowi Kowalskiemu' -> 'Jan Kowalski'\n"
    "- 'Grzegorzowi Wiśniewskiemu' -> 'Grzegorz Wiśniewski'\n"
    "- 'Leszkowi Wieczorkowi' -> 'Leszek Wieczorek'\n"
    "- 'Sebastianowi Baranowi' -> 'Sebastian Baran'\n"
    "- 'Iwonie Rutkowskiej' -> 'Iwona Rutkowska'\n"
    "- 'Annie Nowak' -> 'Anna Nowak'\n"
    "- 'przez adw. Piotra Zielińskiego' -> 'Piotr Zieliński'\n"
    "- 'z Katarzyną Lis' -> 'Katarzyna Lis'"
)

# Repeated after the document text: a small model follows the instruction closest to its answer.
FINAL_REMINDER = (
    "PRZYPOMNIENIE przed odpowiedzią: zwróć wyłącznie obiekt JSON zgodny z szablonem; brakujące dane = null; "
    "każde imię i nazwisko w MIANOWNIKU (np. 'Grzegorz Wiśniewski', nie 'Grzegorzowi Wiśniewskiemu')."
)

# Grounding: how a model value is checked against the document text.
_DIGIT_TYPES = {"nip", "regon", "krs", "pesel", "iban_pl"}
_EXACT_TYPES = {"bzp", "ted", "reference", "email"}
_WORD_TYPES = {"text", "person", "company", "place"}


# --- prompt ---------------------------------------------------------------------------------


EVIDENCE_SUFFIX = "_cytat"
"""Auxiliary key the model fills BEFORE a field with `llm_evidence` (never written to output)."""


def _skeleton(node: Any) -> Any:
    if isinstance(node, FieldSpec):
        return None
    if isinstance(node, ListSpec):
        return [_skeleton(node.item)]
    out: dict[str, Any] = {}
    for key, child in node.items():
        if isinstance(child, FieldSpec) and child.llm_evidence:
            out[f"{key}{EVIDENCE_SUFFIX}"] = None
        out[key] = _skeleton(child)
    return out


def _allowed_values(doc_type: DocumentType, container: dict, key: str) -> str | None:
    """For a field that feeds a lookup (e.g. czynnosc_powod_id -> czynnosc_opis), list the dictionary."""
    for sibling in container.values():
        if isinstance(sibling, FieldSpec):
            for strategy in sibling.extract:
                if isinstance(strategy, LookupStrategy) and strategy.source == key:
                    entries = doc_type.dictionary(strategy.dictionary)
                    return "; ".join(f"{k} = {v}" for k, v in entries.items())
    return None


def _schema_lines(doc_type: DocumentType) -> list[str]:
    lines: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, ListSpec):
            lines.append(f"- {path}: lista{' — ' + node.description if node.description else ''}")
            walk(node.item, f"{path}[]")
            return
        for key, child in node.items():
            child_path = f"{path}.{key}" if path else key
            if isinstance(child, FieldSpec):
                if child.is_dependent:
                    continue  # computed by the application, the model may leave it null
                if child.llm_evidence:
                    lines.append(
                        f"- {child_path}{EVIDENCE_SUFFIX}: najpierw przepisz dosłownie zdanie z dokumentu, "
                        f"na podstawie którego ustalasz pole {key} (uzupełnij przed polem {key})"
                    )
                line = f"- {child_path}: {TYPE_HINTS.get(child.type, child.type)}"
                if child.description:
                    line += f" — {child.description}"
                if allowed := _allowed_values(doc_type, node, key):
                    line += f" Dozwolone wartości: {allowed}."
                lines.append(line)
            else:
                walk(child, child_path)

    walk(doc_type.output, "")
    return lines


def build_messages(doc: IngestedDocument, doc_type: DocumentType, max_chars: int) -> list[dict[str, str]]:
    text = doc.full_text()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[... dalsza część dokumentu pominięta ...]"
    user = (
        f"Typ dokumentu: {doc_type.name} — {doc_type.description or ''}\n\n"
        "Pola do wypełnienia (ścieżka: format — opis):\n"
        + "\n".join(_schema_lines(doc_type))
        + "\n\nSzablon JSON (wypełnij wartości; listy powtórz dla każdego elementu):\n"
        + json.dumps(_skeleton(doc_type.output), ensure_ascii=False, indent=1)
        + "\n\nTreść dokumentu (strony oznaczone '=== Strona N ==='):\n"
        + text
        + "\n\n"
        + FINAL_REMINDER
    )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def parse_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise LLMError("odpowiedź modelu nie zawiera JSON") from None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMError(f"niepoprawny JSON w odpowiedzi modelu: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMError("odpowiedź modelu nie jest obiektem JSON")
    return data


# --- validation -------------------------------------------------------------------------------


class _Grounding:
    def __init__(self, doc: IngestedDocument):
        text = doc.full_text(page_markers=False)
        self.digits = re.sub(r"\D", "", text)
        self.folded = fold(text)
        self.compact = re.sub(r"\s+", "", self.folded)

    def check(self, value_type: str, value: Any) -> bool:
        if value_type in _DIGIT_TYPES:
            return str(value) in self.digits
        if value_type in _EXACT_TYPES:
            return re.sub(r"\s+", "", fold(str(value))) in self.compact
        if value_type in _WORD_TYPES:
            # Word stems (first 4 letters) tolerate Polish declension: "Kowalskiemu" ~ "Kowalski".
            words = [w for w in re.findall(r"\w{3,}", fold(str(value)))]
            if not words:
                return False
            found = sum(1 for w in words if w[:4] in self.folded)
            return found / len(words) >= 0.8
        return True  # dates, amounts, integers: validated by the normalizer only


def _as_raw(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def validate_value(spec: FieldSpec, value: Any, grounding: _Grounding) -> tuple[Any, str | None]:
    """(normalized value, None) or (None, reason it was rejected)."""
    if value is None or value == "" or isinstance(value, (dict, list)):
        return None, None
    normalized = VALUE_TYPES[spec.type].normalize(_as_raw(value))
    if normalized is None:
        return None, f"AI: nieprawidłowy format '{value}'"
    if reason := spec.plausible(normalized):
        return None, f"AI: {reason}"
    checksum = spec.effective_checksum()
    if checksum and isinstance(normalized, str) and not CHECKSUMS[checksum](normalized) and spec.on_invalid_checksum == "reject":
        return None, f"AI: zła suma kontrolna {normalized}"
    if not grounding.check(spec.type, normalized):
        return None, f"AI: wartości '{normalized}' nie ma w treści dokumentu"
    return normalized, None


# --- merge ------------------------------------------------------------------------------------


# Endings of Polish oblique cases in names ("Leszkowi Wieczorkowi", "Iwonie Rutkowskiej",
# "Piotra Zielińskiego", "z Katarzyną"). Only used as a GATE: the model may replace a rule
# name only when the rule name looks declined — the code never declines names itself.
_DECLINED_ENDINGS = ("owi", "emu", "iemu", "ej", "iej", "ego", "iego", "ą", "em", "iem")


def _looks_declined(name: str) -> bool:
    return any(word.endswith(_DECLINED_ENDINGS) for word in re.findall(r"\w+", str(name).casefold()))


def _words(value: Any) -> list[str]:
    return re.findall(r"\w+", str(value))


ARBITER_PROMPT = (
    "Jesteś weryfikatorem danych wyciągniętych z polskiego dokumentu prawnego. Dwa źródła podały różne "
    "wartości tego samego pola. Na podstawie fragmentów dokumentu wybierz wartość poprawną zgodnie z opisem "
    'pola. Odpowiedz WYŁĄCZNIE obiektem JSON: {"wybor": "A"} albo {"wybor": "B"}.'
)


class _Merger:
    def __init__(
        self,
        doc_type: DocumentType,
        traces: dict[str, FieldTrace],
        grounding: _Grounding,
        model: str,
        doc_text: str = "",
        arbiter: Any = None,
    ):
        self.doc_type = doc_type
        self.traces = traces
        self.grounding = grounding
        self.rule = f"LLM {model}"
        self.doc_text = doc_text
        self.arbiter = arbiter
        """LLM client used to settle `arbitrate` conflicts (None = keep the rule value)."""

    # --- fields ---------------------------------------------------------------------------

    def _gate(self, spec: FieldSpec, rule_value: Any, value: Any) -> str | None:
        """Type-specific reasons not to let a model value replace / fill a field."""
        if spec.type == "person":
            if len(_words(value)) > 3 or "," in str(value) or " i " in str(value):
                return f"AI: '{value}' to więcej niż jedna osoba"
            if rule_value is not None and value != rule_value:
                if len(_words(value)) != len(_words(rule_value)):
                    return f"AI: '{value}' ma inną liczbę wyrazów niż '{rule_value}'"
                if not _looks_declined(rule_value):
                    return f"AI: reguła ma już mianownik ('{rule_value}'), pominięto '{value}'"
        return None

    def _arbitrate(
        self, spec: FieldSpec, rule_value: Any, value: Any, path: str, allowed: str | None, evidence: str | None
    ) -> Any:
        trace = self.traces.get(path)
        rule_snippet = (trace.snippet if trace else None) or "(brak)"
        user = (
            f"Pole: {path}\nOpis pola: {spec.description or ''}\n"
            + (f"Dozwolone wartości: {allowed}\n" if allowed else "")
            + f"\nKandydat A: {rule_value}\nFragment, na podstawie którego wskazano A:\n{rule_snippet}\n"
            + f"\nKandydat B: {value}\nFragment, na podstawie którego wskazano B:\n{evidence or '(brak)'}\n"
            + f"\nPoczątek dokumentu:\n{self.doc_text[:6000]}"
        )
        try:
            response = self.arbiter.chat(
                [{"role": "system", "content": ARBITER_PROMPT}, {"role": "user", "content": user}],
                max_tokens=20,
                temperature=0.0,
                json_mode=True,
            )
            choice = str(parse_json(response.text).get("wybor", "")).strip().upper()
        except LLMError as exc:
            if trace is not None:
                trace.warnings.append(f"AI-arbiter niedostępny ({exc}); zostaje reguła")
            return rule_value
        if choice == "B":
            self.traces[path] = FieldTrace(
                value=value,
                method="llm",
                rule=f"{self.rule} (arbitraż)",
                snippet=evidence,
                raw=value,
                warnings=[f"reguła: {rule_value} — arbiter wybrał AI"],
            )
            return value
        if trace is not None:
            trace.warnings.append(f"AI podaje {value}; arbiter wybrał regułę")
        return rule_value

    def field(
        self,
        spec: FieldSpec,
        rule_value: Any,
        llm_value: Any,
        path: str,
        evidence: str | None = None,
        allowed: str | None = None,
    ) -> Any:
        if spec.is_dependent or spec.llm == "never":
            return rule_value
        value, problem = validate_value(spec, llm_value, self.grounding)
        if value is not None and (reason := self._gate(spec, rule_value, value)):
            value, problem = None, reason
        trace = self.traces.get(path)
        if value is None:
            if problem and trace is not None:
                trace.warnings.append(problem)
            return rule_value
        if rule_value is not None and value != rule_value and spec.llm == "arbitrate":
            if self.arbiter is not None:
                return self._arbitrate(spec, rule_value, value, path, allowed, evidence)
            if trace is not None:
                trace.warnings.append(f"AI podaje inną wartość: {value} (bez arbitrażu zostaje reguła)")
            return rule_value
        if rule_value is None or spec.llm == "prefer":
            previous = f"reguła: {rule_value}" if rule_value is not None and rule_value != value else None
            self.traces[path] = FieldTrace(
                value=value,
                method="llm",
                rule=self.rule,
                snippet=evidence,
                raw=llm_value,
                warnings=[previous] if previous else [],
            )
            return value
        if trace is not None:
            trace.warnings.append("AI zgodne z regułą" if value == rule_value else f"AI podaje inną wartość: {value}")
            if value == rule_value:
                trace.method = "rule+llm"
        return rule_value

    # --- containers -------------------------------------------------------------------------

    def node(self, node: Any, rule_value: Any, llm_value: Any, path: str) -> Any:
        if isinstance(node, FieldSpec):
            return self.field(node, rule_value, llm_value, path)
        if isinstance(node, ListSpec):
            return self.list(node, rule_value or [], llm_value if isinstance(llm_value, list) else [], path)
        rule_dict = rule_value if isinstance(rule_value, dict) else {}
        llm_dict = llm_value if isinstance(llm_value, dict) else {}
        out = {}
        for key, child in node.items():
            child_path = f"{path}.{key}" if path else key
            if isinstance(child, FieldSpec):
                evidence = llm_dict.get(f"{key}{EVIDENCE_SUFFIX}") if child.llm_evidence else None
                out[key] = self.field(
                    child,
                    rule_dict.get(key),
                    llm_dict.get(key),
                    child_path,
                    evidence=str(evidence) if evidence else None,
                    allowed=_allowed_values(self.doc_type, node, key),
                )
            else:
                out[key] = self.node(child, rule_dict.get(key), llm_dict.get(key), child_path)
        return out

    def _key(self, spec: ListSpec, item: Any, normalize: bool = False) -> tuple | None:
        """Identity of a list item from its `unique_by` fields (model values normalized first)."""
        if not spec.unique_by or not isinstance(item, dict):
            return None
        key = []
        for field_path in spec.unique_by:
            value: Any = item
            node: Any = spec.item
            for part in field_path.split("."):
                value = value.get(part) if isinstance(value, dict) else None
                node = node.get(part) if isinstance(node, dict) else None
            if normalize and value is not None and isinstance(node, FieldSpec):
                value = VALUE_TYPES[node.type].normalize(_as_raw(value))
            key.append(_stems(value) if value is not None else None)
        return tuple(key) if any(k is not None for k in key) else None

    def _redistribute(self, spec: ListSpec, pairs: list[tuple[Any, Any]]) -> list[tuple[Any, Any]]:
        """Document-scope nested lists (e.g. signers of each consortium member): rules cannot tell
        who signed for whom and list everyone under the first parent. When the model distributes
        the SAME people among the parents, its distribution is used instead."""
        if not isinstance(spec.item, dict) or len(pairs) < 2 or any(not isinstance(m, dict) for _, m in pairs):
            return pairs
        for key, child in spec.item.items():
            if not (isinstance(child, ListSpec) and child.scope == "document"):
                continue
            rule_people = sorted(self._key(child, i) or () for r, _ in pairs for i in (r or {}).get(key) or [])
            llm_people = sorted(self._key(child, i, normalize=True) or () for _, m in pairs for i in m.get(key) or [])
            if rule_people and rule_people == llm_people:
                pairs = [({**r, key: []} if isinstance(r, dict) else r, m) for r, m in pairs]
        return pairs

    def list(self, spec: ListSpec, rule_items: list, llm_items: list, path: str) -> list:
        llm_items = [i for i in llm_items if i is not None]
        if not rule_items:
            pairs = [(None, item) for item in llm_items]
        else:
            # Pair rule items with model items: by identifying fields, or by position when the counts agree.
            remaining = list(llm_items)
            pairs = []
            for rule_item in rule_items:
                match = None
                key = self._key(spec, rule_item)
                if key is not None:
                    match = next((m for m in remaining if self._key(spec, m, normalize=True) == key), None)
                elif len(rule_items) == len(llm_items):
                    match = llm_items[len(pairs)]
                if match is not None and match in remaining:
                    remaining.remove(match)
                pairs.append((rule_item, match))
            # Items the rules did not find are NOT added: the model often repeats an item in
            # another form (e.g. a declined name), which would create false duplicates.
            pairs = self._redistribute(spec, pairs)

        merged = []
        for rule_item, llm_item in pairs:
            index_path = f"{path}[{len(merged)}]"
            value = self.node(spec.item, rule_item, llm_item, index_path)
            if rule_item is None and _is_blank(value):
                continue
            merged.append(value)
        return merged[: spec.max_items]


def _stems(value: Any) -> str:
    """Declension-tolerant identity: first 4 letters of each word
    ("Janowi Kowalskiemu" and "Jan Kowalski" -> "jan kowa")."""
    return " ".join(word[:4] for word in re.findall(r"\w+", fold(str(value))))


def _is_blank(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_is_blank(v) for v in value.values())
    if isinstance(value, list):
        return all(_is_blank(v) for v in value)
    return value is None


def _remove_dropped_traces(traces: dict[str, FieldTrace], data: dict[str, Any]) -> None:
    """Traces of model-only list items that were dropped must not stay in the metadata."""
    existing: set[str] = set()

    def walk(value: Any, path: str) -> None:
        existing.add(path)
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                walk(v, f"{path}[{i}]")

    walk(data, "")
    for path in list(traces):
        if path not in existing:
            del traces[path]


def merge(
    rule_result: ExtractionResult,
    llm_data: dict[str, Any],
    doc: IngestedDocument,
    doc_type: DocumentType,
    model: str,
    arbiter: Any = None,
) -> ExtractionResult:
    """`arbiter`: LLM client for `llm: arbitrate` conflicts (None = the rule value is kept)."""
    traces = {path: trace.model_copy(deep=True) for path, trace in rule_result.fields.items()}
    merger = _Merger(doc_type, traces, _Grounding(doc), model, doc.full_text(), arbiter)
    data = merger.node(doc_type.output, rule_result.data, llm_data, "")
    apply_dependents(doc_type, data, traces)
    _remove_dropped_traces(traces, data)
    return ExtractionResult(document_type=doc_type.name, data=data, fields=traces)


def empty_result(doc_type: DocumentType) -> ExtractionResult:
    """Rule-free starting point for the `llm` mode."""
    return ExtractionResult(document_type=doc_type.name, data=_empty(doc_type.output), fields={})


def _empty(node: Any) -> Any:
    if isinstance(node, FieldSpec):
        return None
    if isinstance(node, ListSpec):
        return []
    return {key: _empty(child) for key, child in node.items()}


def has_gaps(result: ExtractionResult, doc_type: DocumentType) -> bool:
    """True when asking the model can change the result: a fillable field is empty, or a
    field's policy is `prefer` (the model's answer wins over the rules)."""

    def walk(node: Any, value: Any) -> bool:
        if isinstance(node, FieldSpec):
            if node.is_dependent or node.llm == "never":
                return False
            return value is None or node.llm in ("prefer", "arbitrate")
        if isinstance(node, ListSpec):
            return not value or any(walk(node.item, item) for item in value)
        return any(walk(child, (value or {}).get(key)) for key, child in node.items())

    return walk(doc_type.output, result.data)


def llm_extract(
    doc: IngestedDocument, doc_type: DocumentType, client: LLMClient, max_chars: int, max_tokens: int
) -> tuple[dict[str, Any], ChatResponse]:
    messages = build_messages(doc, doc_type, max_chars)
    response = client.chat(messages, max_tokens=max_tokens, temperature=0.0, json_mode=True)
    return parse_json(response.text), response
