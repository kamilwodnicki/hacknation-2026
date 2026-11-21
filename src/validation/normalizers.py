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
    r"(?<![\d.,])\d{1,3}(?:[  .]\d{3})+(?:,\d{2})?(?![.,]?\d)"
    r"|(?<![\d.,])\d+(?:[.,]\d{2})?(?![.,]?\d)"
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
    return s or None


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
}
