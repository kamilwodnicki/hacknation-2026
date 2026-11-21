"""PDF -> text, page by page: text layer first, OCR only for pages without usable text."""

import logging
import unicodedata
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium

from src.config import Settings, get_settings
from src.ingestion.models import IngestedDocument, Page, PageSource
from src.ingestion.ocr import ocr_image

log = logging.getLogger(__name__)


class IngestionError(Exception):
    """The file cannot be opened as a PDF (corrupted, encrypted, not a PDF)."""


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").replace("￾", "")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def has_usable_text(text: str, min_chars: int) -> bool:
    return sum(ch.isalnum() for ch in text) >= min_chars


def _render_bgr(page: pdfium.PdfPage, dpi: int) -> np.ndarray:
    rgb = np.asarray(page.render(scale=dpi / 72).to_pil().convert("RGB"))
    return np.ascontiguousarray(rgb[:, :, ::-1])


def read_pdf(
    source: str | Path | bytes,
    filename: str | None = None,
    settings: Settings | None = None,
) -> IngestedDocument:
    """Read a PDF from a path or raw bytes."""
    s = settings or get_settings()
    if filename is None:
        filename = Path(source).name if isinstance(source, (str, Path)) else "document.pdf"
    try:
        pdf = pdfium.PdfDocument(str(source) if isinstance(source, Path) else source)
    except pdfium.PdfiumError as exc:
        raise IngestionError(f"{filename}: cannot open PDF ({exc})") from exc

    pages: list[Page] = []
    ocr_count = 0
    try:
        for index in range(len(pdf)):
            page = pdf[index]
            try:
                textpage = page.get_textpage()
                text = clean_text(textpage.get_text_range())
                textpage.close()

                if has_usable_text(text, s.ocr_min_text_chars):
                    pages.append(Page(number=index + 1, text=text, source=PageSource.TEXT_LAYER))
                elif s.ocr_max_pages and ocr_count >= s.ocr_max_pages:
                    pages.append(Page(number=index + 1, text="", source=PageSource.SKIPPED))
                else:
                    ocr_text, confidence = ocr_image(_render_bgr(page, s.ocr_dpi))
                    ocr_count += 1
                    pages.append(
                        Page(
                            number=index + 1,
                            text=clean_text(ocr_text),
                            source=PageSource.OCR,
                            ocr_confidence=confidence,
                        )
                    )
            finally:
                page.close()
    finally:
        pdf.close()

    doc = IngestedDocument(filename=filename, pages=pages)
    log.info("%s: %d pages, OCR on %s", filename, doc.page_count, doc.ocr_pages or "none")
    return doc
