"""The YAML example in docs/nowy-typ-dokumentu.md is valid and works as described."""

import re
from pathlib import Path

import yaml

from src.classification import classify
from src.extraction import DocumentType, extract
from src.ingestion import IngestedDocument, Page, PageSource

ROOT = Path(__file__).resolve().parents[1]


def example_type() -> DocumentType:
    text = (ROOT / "docs" / "nowy-typ-dokumentu.md").read_text(encoding="utf-8")
    block = re.search(r"```yaml\n(.*?)```", text, re.DOTALL).group(1)
    return DocumentType.model_validate(yaml.safe_load(block))


def test_documented_example_extracts_data():
    t = example_type()
    doc = IngestedDocument(
        filename="z.pdf",
        pages=[
            Page(
                number=1,
                source=PageSource.TEXT_LAYER,
                text=(
                    "Kraków, dnia 5 marca 2026 r.\n"
                    "Zawiadomienie o wyborze najkorzystniejszej oferty\n"
                    "Znak sprawy: ZP.271.5.2026\n"
                    "Zamawiający informuje, że wybrana została oferta wykonawcy Alfa Serwis sp. z o.o.\n"
                    "Cena oferty: 120 000,00 zł\n"
                    "Punktacja:\n"
                    "Alfa Serwis sp. z o.o. – 100 pkt\n"
                    "Beta Budownictwo S.A. – 87,5 pkt"
                ),
            )
        ],
    )
    assert classify(doc, {t.name: t}).document_type == "zawiadomienie_wybor"
    data = extract(doc, t).data
    assert data["Zawiadomienie"] == {
        "data": "2026-03-05",
        "numer_postepowania": "ZP.271.5.2026",
        "wybrany_wykonawca": "Alfa Serwis sp. z o.o.",
        "cena": 120000.0,
    }
    assert data["Oferty"] == [
        {"wykonawca": "Alfa Serwis sp. z o.o.", "punkty": 100.0},
        {"wykonawca": "Beta Budownictwo S.A.", "punkty": 87.5},
    ]
