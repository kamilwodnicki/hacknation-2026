"""Tests never call a paid LLM API: the provider is forced off before settings are read.
LLM behaviour is tested with a fake client (tests/test_llm.py)."""

import os

os.environ["LLM_PROVIDER"] = "none"


def transfer_pdf(case):
    """Transfer confirmation of a training case — the organizer renamed some files
    from potwierdzenie_przelewu.pdf to przelew.pdf."""
    for name in ("potwierdzenie_przelewu.pdf", "przelew.pdf"):
        if (case / name).exists():
            return case / name
    return case / "potwierdzenie_przelewu.pdf"


def without_account_prefix(data):
    """Organizer reference JSONs omit the "PL" prefix of account numbers, which (per the
    organizer, Discord 2026-11-21) is an error in the references: the output keeps the number
    as written in the document. Compare transfers with the prefix stripped."""
    bank = (data or {}).get("przelew_bankowy")
    if isinstance(bank, dict):
        for key in ("na_rachunek", "z_rachunku"):
            if isinstance(bank.get(key), str):
                bank[key] = bank[key].removeprefix("PL")
    return data
