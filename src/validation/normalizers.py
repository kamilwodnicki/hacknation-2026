"""Value types usable in document-type YAML (`type:`).

Each type defines a regex that locates a candidate value in text and a function that
normalizes it to the output format required by UZP. A normalizer returns None when the
candidate is not a valid value of that type (it is then not used — never guessed).
New document classes compose these generic types in YAML; no code is needed per class.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

_MONTHS = {
    "stycznia": 1, "styczeń": 1, "styczen": 1, "sty": 1,
    "lutego": 2, "luty": 2, "lut": 2,
    "marca": 3, "marzec": 3, "mar": 3,
    "kwietnia": 4, "kwiecień": 4, "kwiecien": 4, "kwi": 4,
    "maja": 5, "maj": 5,
    "czerwca": 6, "czerwiec": 6, "cze": 6,
    "lipca": 7, "lipiec": 7, "lip": 7,
    "sierpnia": 8, "sierpień": 8, "sierpien": 8, "sie": 8,
    "września": 9, "wrzesień": 9, "wrzesnia": 9, "wrzesien": 9, "wrz": 9,
    "października": 10, "październik": 10, "pazdziernika": 10, "paź": 10, "paz": 10,
    "listopada": 11, "listopad": 11, "lis": 11,
    "grudnia": 12, "grudzień": 12, "grudzien": 12, "gru": 12,
}
_MONTH_ALT = "|".join(sorted(_MONTHS, key=len, reverse=True))

DATE_PATTERN = (
    r"\d{4}-\d{1,2}-\d{1,2}"
    r"|\d{1,2}[./-]\d{1,2}[./-]\d{4}"
    rf"|\d{{1,2}}\s+(?:{_MONTH_ALT})\.?\s+\d{{4}}"
)


def normalize_date(raw: str) -> str | None:
    s = raw.strip().lower()
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s):
        y, mo, d = m.groups()
    elif m := re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", s):
        d, mo, y = m.groups()
    elif m := re.fullmatch(rf"(\d{{1,2}})\s+({_MONTH_ALT})\.?\s+(\d{{4}})", s):
        d, month_name, y = m.groups()
        mo = _MONTHS[month_name]
    else:
        return None
    try:
        return date(int(y), int(mo), int(d)).isoformat()
    except ValueError:
        return None


# "10 000,00" / "1.234,56" (thousand separators) or plain "200,00" / "34.00" / "17"
AMOUNT_PATTERN = (
    # Not inside a word: in "CEN9057564440515" (a reference) there is no amount.
    r"(?<![\w.,])\d{1,3}(?:[  .]\d{3})+(?:,\d{2})?(?![.,]?\d)"
    r"|(?<![\w.,])\d+(?:[.,]\d{2})?(?![.,]?\d)"
)


def normalize_amount(raw: str) -> float | None:
    s = raw.replace(" ", " ").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if re.search(r",\d{1,2}$", s) else s.replace(",", "")
    elif s.count(".") > 1 or re.search(r"\.\d{3}$", s):
        s = s.replace(".", "")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def _digits_only(raw: str) -> str:
    return re.sub(r"\D", "", raw)


def _fixed_digits(lengths: tuple[int, ...]) -> Callable[[str], str | None]:
    def normalize(raw: str) -> str | None:
        digits = _digits_only(raw)
        return digits if len(digits) in lengths else None

    return normalize


def normalize_ted(raw: str) -> str | None:
    s = raw.strip()
    if m := re.search(r"(\d{4})\s*/\s*S\s*\d{1,3}\s*-\s*(\d{5,6})", s):
        return f"{int(m.group(2)):06d}-{m.group(1)}"
    if m := re.search(r"(\d{5,6})\s*-\s*(\d{4})", s):
        return f"{int(m.group(1)):06d}-{m.group(2)}"
    return None


def normalize_bzp(raw: str) -> str | None:
    m = re.search(r"(\d{4})\s*/\s*BZP\s*(\d{8})(?:\s*/\s*(\d{1,2}))?", raw, re.IGNORECASE)
    if not m:
        return None
    return f"{m.group(1)}/BZP{m.group(2)}" + (f"/{m.group(3)}" if m.group(3) else "")


def normalize_text(raw: str) -> str | None:
    s = re.sub(r"\s+", " ", raw).strip(" \t:;,")
    # A value quoted inside a sentence: „...”. / "..." -> without the quotes and final dot
    if m := re.fullmatch(r"[„\"“«»](.+?)[”\"«»]\.?", s):
        s = m.group(1).strip()
    # OCR reads the "o" of the legal form as zero: "Sp. z 0.0." -> "Sp. z o.o."
    s = re.sub(r"(?i)\b(sp\.\s?z\s?)[o0]\.\s?[o0]\.", r"\1o.o.", s)
    return s or None


def normalize_integer(raw: str) -> int | None:
    digits = raw.strip()
    return int(digits) if digits.isdigit() else None


def normalize_email(raw: str) -> str | None:
    s = raw.strip().strip(".,;:()<>").lower()
    return s if re.fullmatch(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", s) else None


# Capitalized words that are not first names / surnames (headings, roles, institutions).
_NOT_NAME_WORDS = {
    "kancelaria", "kancelarii", "prawna", "prawny", "prawnego", "adwokacka", "radca", "radcy", "radcę",
    "spółka", "zarząd", "zarządu", "prezes", "członek", "prokurent", "wiceprezes", "pełnomocnik",
    "krajowa", "krajowej", "izba", "izby", "odwoławcza", "odwoławczej", "sąd", "urząd", "gmina",
    "miasto", "powiat", "województwo", "dział", "dyrektor", "zamawiający", "odwołujący", "wykonawca",
    "mocodawca", "data", "strona", "podpis", "pieczęć", "adres", "ulica",
}


def normalize_person(raw: str) -> str | None:
    s = normalize_text(raw)
    if not s or any(word.casefold() in _NOT_NAME_WORDS for word in re.split(r"[\s-]+", s)):
        return None
    return s


def normalize_company(raw: str) -> str | None:
    s = normalize_text(raw)
    return s.strip("„”\"") if s else None


_UPPER = "A-ZĄĆĘŁŃÓŚŹŻ"
_LOWER = "a-ząćęłńóśźż"
_NAME_WORD = rf"[{_UPPER}][{_LOWER}]+(?:-[{_UPPER}][{_LOWER}]+)?"
_LEGAL_FORM = "|".join(
    [
        r"sp\.\s?z\s?[o0]\.\s?[o0]\.(?:\s?sp\.\s?k\.)?",  # 0: OCR misread of "o"
        r"spółka z ograniczoną odpowiedzialnością(?: spółka komandytowa)?",
        r"S\.A\.",
        r"spółka akcyjna",
        r"sp\.\s?j\.?",
        r"spółka jawna",
        r"sp\.\s?k\.?",
        r"spółka komandytowa",
        r"sp\.\s?p\.?",
        r"spółka partnerska",
        r"S\.K\.A\.",
        r"spółka komandytowo-akcyjna",
    ]
)


def expand_placeholders(pattern: str, value_type: str | None) -> str:
    """Replace `{value}` (the field's own type) and `{<type>}` (any type) with the type's
    regex, as a non-capturing group. Other braces (quantifiers like `{2,5}`) are kept."""

    def replace(m: re.Match[str]) -> str:
        name = value_type if m.group(1) == "value" else m.group(1)
        if name and name in VALUE_TYPES:
            return f"(?:{VALUE_TYPES[name].pattern})"
        return m.group(0)

    return re.sub(r"\{([a-z_]+)\}", replace, pattern)


def fold(text: str) -> str:
    """Case-, whitespace- and diacritics-insensitive form ("Pełnomocnictwo" -> "pelnomocnictwo")."""
    import unicodedata

    # "ı" (dotless i) is a frequent OCR misread of "i" and has no Unicode decomposition.
    text = text.casefold().replace("ł", "l").replace("ı", "i")
    text = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class ValueType:
    pattern: str
    normalize: Callable[[str], object]
    checksum: str | None = None
    """Name from src.validation.checksums.CHECKSUMS applied to the normalized value."""


VALUE_TYPES: dict[str, ValueType] = {
    "date": ValueType(DATE_PATTERN, normalize_date),
    "amount": ValueType(AMOUNT_PATTERN, normalize_amount),
    # Digit groups may be separated by a space or a line break (wrapped account number).
    "iban_pl": ValueType(r"(?<![\dA-Z])(?:PL)?\s?\d{2}(?:\s?\d{4}){6}(?!\d)", _fixed_digits((26,)), "iban_pl"),
    "nip": ValueType(r"(?<!\d)\d{3}[- ]?\d{3}[- ]?\d{2}[- ]?\d{2}(?!\d)|(?<!\d)\d{3}[- ]?\d{2}[- ]?\d{2}[- ]?\d{3}(?!\d)", _fixed_digits((10,)), "nip"),
    "regon": ValueType(r"(?<!\d)\d{9}(?:\d{5})?(?!\d)", _fixed_digits((9, 14)), "regon"),
    "krs": ValueType(r"(?<!\d)\d{10}(?!\d)", _fixed_digits((10,)), "krs"),
    "pesel": ValueType(r"(?<!\d)\d{11}(?!\d)", _fixed_digits((11,)), "pesel"),
    "ted": ValueType(r"\d{4}\s*/\s*S\s*\d{1,3}\s*-\s*\d{5,6}|(?<!\d)\d{5,6}-\d{4}(?!\d)", normalize_ted),
    "bzp": ValueType(r"\d{4}\s*/\s*BZP\s*\d{8}(?:\s*/\s*\d{1,2})?", normalize_bzp),
    # Identifier such as "CEN2604016344389" or "ZP.039.2025": must contain a digit.
    "reference": ValueType(
        r"(?<![\w/.-])(?=[A-Za-z/._-]*\d)[A-Z0-9][A-Za-z0-9/._-]{4,}[A-Za-z0-9](?![\w/-])", normalize_text
    ),
    "text": ValueType(r".+", normalize_text),
    "integer": ValueType(r"(?<!\d)\d+(?!\d)", normalize_integer),
    # Town name: "Kraków", "Zielona Góra", "Bielsko-Biała", "Ostrów Mazowiecka".
    "place": ValueType(rf"(?-i:[{_UPPER}][{_LOWER}]+(?:[ -][{_UPPER}][{_LOWER}]+){{0,2}})(?!\w)", normalize_text),
    "email": ValueType(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", normalize_email),
    # "Jan Kowalski", "Anna Nowak-Kowalska" (capitalized words; case-sensitive even when
    # the surrounding search ignores case).
    "person": ValueType(rf"(?-i:{_NAME_WORD}\s+{_NAME_WORD}(?!\w))", normalize_person),
    # Company name ending with a Polish legal form: "Hartica Serwis S.A.", "X sp. z o.o.".
    # A line break is allowed inside (names wrapped by the layout).
    "company": ValueType(
        rf"(?-i:[A-ZĄĆĘŁŃÓŚŹŻ0-9„\"])[^,;:()„”]{{0,120}}?\s(?:{_LEGAL_FORM})(?!\w)", normalize_company
    ),
}
