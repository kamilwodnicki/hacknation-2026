"""HTTP API (FastAPI). Interactive docs: http://localhost:8000/docs

    GET  /health            — liveness check
    GET  /document-types    — document types loaded from config/document_types
    POST /extract           — upload one PDF, get the UZP JSON and extraction metadata
"""

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from src.pipeline import PipelineResult, document_types, process_pdf

app = FastAPI(
    title="Odwołania2json",
    version="0.1.0",
    description="Ekstrakcja danych z dokumentów spraw odwoławczych KIO (PDF) do JSON w formacie UZP.",
)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class DocumentTypeInfo(BaseModel):
    name: str
    description: str | None
    fields: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/document-types")
def list_document_types() -> list[DocumentTypeInfo]:
    return [
        DocumentTypeInfo(name=t.name, description=t.description, fields=list(t.fields()))
        for t in document_types().values()
    ]


@app.post("/extract")
def extract_pdf(
    file: UploadFile = File(..., description="Plik PDF"),
    include_text: bool = Query(False, description="Dołącz tekst stron (podgląd w UI)"),
) -> PipelineResult:
    """`output` is exactly the JSON written to the output folder ({} = document not recognized);
    the other fields explain how it was obtained. Runs in a worker thread (sync endpoint)."""
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Plik jest za duży (limit 50 MB).")
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="To nie jest plik PDF.")
    return process_pdf(content, filename=file.filename or "document.pdf", include_text=include_text)
