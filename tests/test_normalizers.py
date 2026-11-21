import re

import pytest

from src.validation.checksums import iban_pl_valid, nip_valid, pesel_valid, regon_valid
from src.validation.normalizers import VALUE_TYPES, normalize_amount, normalize_bzp, normalize_date, normalize_ted, normalize_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-08-12", "2026-08-12"),
        ("04-07-2026", "2026-07-04"),
        ("10.03.2026", "2026-03-10"),
        ("1/2/2026", "2026-02-01"),
        ("23 sierpnia 2026", "2026-08-23"),
        ("16 czerwca 2025", "2025-06-16"),
        ("5 Października 2025", "2025-10-05"),
        ("31.02.2026", None),
        ("2026/08/12", None),
    ],
)
def test_normalize_date(raw, expected):
    assert normalize_date(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("200,00", 200.0),
        ("34.00", 34.0),
        ("17", 17.0),
        ("10 000,00", 10000.0),
        ("1.234,56", 1234.56),
        ("1,234.56", 1234.56),
        ("15 000,50", 15000.5),
    ],
)
def test_normalize_amount(raw, expected):
    assert normalize_amount(raw) == expected


def test_amount_pattern_does_not_split_dates():
    assert re.search(VALUE_TYPES["amount"].pattern, "PLN 34.00").group(0) == "34.00"
    assert re.search(VALUE_TYPES["amount"].pattern, "kwota 10 000,00 zł").group(0) == "10 000,00"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("641651-2025", "641651-2025"), ("2025/S 123-641651", "641651-2025"), ("2025/S 5-41651", "041651-2025")],
)
def test_normalize_ted(raw, expected):
    assert normalize_ted(raw) == expected


def test_normalize_bzp():
    assert normalize_bzp("2025/BZP 00270698") == "2025/BZP00270698"
    assert normalize_bzp("2025/BZP 00270698/01") == "2025/BZP00270698/01"


def test_normalize_text_strips_quotes_and_whitespace():
    assert normalize_text("  „opłata\nskarbowa”. ") == "opłata skarbowa"
    assert normalize_text("BUDOWA DR. POŻAR.") == "BUDOWA DR. POŻAR."
    assert normalize_text("   ") is None


def test_iban_digits():
    assert VALUE_TYPES["iban_pl"].normalize("PL61 1090 1014 0000 0712 1981 2874") == "61109010140000071219812874"
    assert VALUE_TYPES["iban_pl"].normalize("PL61 1090") is None


def test_reference_requires_a_digit():
    m = re.search(VALUE_TYPES["reference"].pattern, "operacji: CEN2611091860728.")
    assert m.group(0) == "CEN2611091860728"


def test_checksums():
    assert nip_valid("5540240549")
    assert not nip_valid("5540240548")
    assert regon_valid("000279077")
    assert not regon_valid("000279078")
    assert pesel_valid("44051401359")
    assert not pesel_valid("44051401358")
    assert iban_pl_valid("61109010140000071219812874")
    assert not iban_pl_valid("61109010140000071219812875")
