"""The whole processing chain for one PDF, shared by the CLI, the API and the UI:

    PDF -> ingestion (text layer / OCR) -> classification -> extraction -> result

The result holds the output JSON in the exact UZP format (`output`, empty dict for an
unrecognized document) and the metadata explaining how it was obtained.
"""

import logging
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.classification import ClassificationResult, classify
from src.config import Settings, get_settings
from src.extraction import DocumentType, FieldTrace, extract, load_document_types
from src.ingestion import IngestedDocument, IngestionError, read_pdf

log = logging.getLogger(__name__)

# OCR and ONNX Runtime already use all CPU cores; processing documents one at a time
# keeps memory predictable on a 16 GB laptop and avoids sharing the OCR engine.
_processing_lock = threading.Lock()


class IngestionInfo(BaseModel):
    page_count: int
    ocr_pages: list[int]
    skipped_pages: list[int]


class PipelineResult(BaseModel):
    filename: str
    document_type: str | None
    """None = not recognized (or unreadable) -> empty output JSON."""
    output: dict[str, Any]
    """JSON in the UZP format, written to output/<name>.json."""
    classification: ClassificationResult | None = None
    fields: dict[str, FieldTrace] = {}
    ingestion: IngestionInfo | None = None
    error: str | None = None
    seconds: float = 0.0
    pages_text: list[str] | None = None
    """Extracted text per page (only when requested, e.g. for the UI preview)."""


@lru_cache
def _cached_types(config_dir: str) -> dict[str, DocumentType]:
    return load_document_types(Path(config_dir) / "document_types")


def document_types(settings: Settings | None = None) -> dict[str, DocumentType]:
    """Document types from config/document_types (loaded and validated once)."""
    s = settings or get_settings()
    return _cached_types(str(s.config_dir))


def process_ingested(doc: IngestedDocument, types: dict[str, DocumentType]) -> tuple[ClassificationResult, Any]:
    classification = classify(doc, types)
    if classification.document_type is None:
        return classification, None
    return classification, extract(doc, types[classification.document_type])


def process_pdf(
    source: str | Path | bytes,
    filename: str | None = None,
    settings: Settings | None = None,
    include_text: bool = False,
) -> PipelineResult:
    s = settings or get_settings()
    name = filename or (Path(source).name if isinstance(source, (str, Path)) else "document.pdf")
    start = time.perf_counter()
    with _processing_lock:
        try:
            doc = read_pdf(source, filename=name, settings=s)
        except IngestionError as exc:
            log.warning("%s", exc)
            return PipelineResult(
                filename=name, document_type=None, output={}, error=str(exc), seconds=time.perf_counter() - start
            )
        classification, extraction = process_ingested(doc, document_types(s))

    return PipelineResult(
        filename=name,
        document_type=classification.document_type,
        output=extraction.data if extraction else {},
        classification=classification,
        fields=extraction.fields if extraction else {},
        ingestion=IngestionInfo(page_count=doc.page_count, ocr_pages=doc.ocr_pages, skipped_pages=doc.skipped_pages),
        seconds=round(time.perf_counter() - start, 2),
        pages_text=[p.text for p in doc.pages] if include_text else None,
    )
