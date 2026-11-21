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
