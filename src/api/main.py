"""FastAPI entrypoint. Endpoints for extraction are added in later steps."""

from fastapi import FastAPI

app = FastAPI(title="Odwołania2json", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
