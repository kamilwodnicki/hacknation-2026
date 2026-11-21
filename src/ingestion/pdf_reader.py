"""PDF -> text, page by page: text layer first, OCR only for pages without usable text."""

import hashlib
import json
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


def _cached_ocr(page: pdfium.PdfPage, index: int, source: str | Path | bytes, s: Settings) -> tuple[str, float | None]:
    """OCR of one page, cached on disk by (file content, page, DPI): repeated runs on the same
    scans take seconds instead of minutes. The cache can be deleted at any time."""
    if not s.ocr_cache_dir:
        return ocr_image(_render_bgr(page, s.ocr_dpi))
    content = source if isinstance(source, bytes) else Path(source).read_bytes()
    key = hashlib.sha256(content).hexdigest()
    path = Path(s.ocr_cache_dir) / key[:2] / f"{key}_p{index + 1}_dpi{s.ocr_dpi}.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data["text"], data.get("confidence")
        except (ValueError, KeyError):
            pass  # damaged entry: OCR again
    text, confidence = ocr_image(_render_bgr(page, s.ocr_dpi))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"text": text, "confidence": confidence}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        log.warning("OCR cache not writable: %s", path)
    return text, confidence


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
                    ocr_text, confidence = _cached_ocr(page, index, source, s)
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
