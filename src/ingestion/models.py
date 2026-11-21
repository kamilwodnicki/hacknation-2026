"""Data models produced by the ingestion step."""

from enum import Enum

from pydantic import BaseModel, computed_field


class PageSource(str, Enum):
    TEXT_LAYER = "text_layer"
    OCR = "ocr"
    SKIPPED = "skipped"
    """Scanned page not OCR-ed because of the OCR_MAX_PAGES limit."""


class Page(BaseModel):
    number: int
    """1-based page number."""
    text: str
    source: PageSource
    ocr_confidence: float | None = None
    """Mean recognition score (0-1) for OCR pages."""


class IngestedDocument(BaseModel):
    filename: str
    pages: list[Page]

    @computed_field
    @property
    def page_count(self) -> int:
        return len(self.pages)

    @computed_field
    @property
    def ocr_pages(self) -> list[int]:
        return [p.number for p in self.pages if p.source == PageSource.OCR]

    @computed_field
    @property
    def skipped_pages(self) -> list[int]:
        return [p.number for p in self.pages if p.source == PageSource.SKIPPED]

    def full_text(self, page_markers: bool = True) -> str:
        """Whole document text. Page markers let later steps cite the source page."""
        parts = []
        for p in self.pages:
            if p.source == PageSource.SKIPPED:
                continue
            parts.append(f"=== Strona {p.number} ===\n{p.text}" if page_markers else p.text)
        return "\n\n".join(parts)
