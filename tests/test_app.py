"""End-to-end behaviour of the CLI (input -> output tree) and the HTTP API."""

import json
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.cli import main as cli_main
from src.cli import output_path

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
CASE = DATA_DIR / "dane" / "przyklad_01"
NEGATIVE = DATA_DIR / "szablon-aplikacja" / "input" / "case1" / "negatywny przyklad.pdf"
needs_data = pytest.mark.skipif(not CASE.exists() or not NEGATIVE.exists(), reason="organizer data not mounted")

client = TestClient(app)


def test_output_path_keeps_tree_and_name():
    pdf = Path("/in/case1/sub/Odwołanie nr 1.PDF")
    assert output_path(pdf, Path("/in"), Path("/out")) == Path("/out/case1/sub/Odwołanie nr 1.json")
    assert output_path(pdf, Path("/in"), Path("/meta"), ".meta.json") == Path("/meta/case1/sub/Odwołanie nr 1.meta.json")


def test_cli_missing_input_dir(tmp_path):
    assert cli_main(["process", "--input", str(tmp_path / "nope"), "--output", str(tmp_path / "out")]) == 2


def test_cli_unreadable_pdf_gives_empty_json_and_error_code(tmp_path):
    (tmp_path / "in" / "case1").mkdir(parents=True)
    (tmp_path / "in" / "case1" / "broken.pdf").write_bytes(b"%PDF-1.4 truncated")
    code = cli_main(["process", "--input", str(tmp_path / "in"), "--output", str(tmp_path / "out"), "--no-meta"])
    assert code == 1
    assert json.loads((tmp_path / "out" / "case1" / "broken.json").read_text(encoding="utf-8")) == {}


@needs_data
def test_cli_processes_case_tree(tmp_path):
    input_dir, output_dir, meta_dir = tmp_path / "input", tmp_path / "output", tmp_path / "meta"
    (input_dir / "case1").mkdir(parents=True)
    (input_dir / "case2").mkdir()
    for name in ("odwolanie.pdf", "pelnomocnictwo.pdf", "potwierdzenie_przelewu.pdf"):
        shutil.copy(CASE / name, input_dir / "case1" / name)
    shutil.copy(NEGATIVE, input_dir / "case2" / "ogloszenie.pdf")

    code = cli_main(["process", "--input", str(input_dir), "--output", str(output_dir), "--meta", str(meta_dir)])
    assert code == 0

    written = sorted(str(p.relative_to(output_dir)).replace("\\", "/") for p in output_dir.rglob("*.json"))
    assert written == [
        "case1/odwolanie.json",
        "case1/pelnomocnictwo.json",
        "case1/potwierdzenie_przelewu.json",
        "case2/ogloszenie.json",
    ]
    przelew = json.loads((output_dir / "case1" / "potwierdzenie_przelewu.json").read_text(encoding="utf-8"))
    assert przelew == json.loads((CASE / "przelew.json").read_text(encoding="utf-8-sig"))
    assert json.loads((output_dir / "case2" / "ogloszenie.json").read_text(encoding="utf-8")) == {}

    meta = json.loads((meta_dir / "case1" / "odwolanie.meta.json").read_text(encoding="utf-8"))
    assert meta["document_type"] == "odwolanie"
    assert meta["fields"]["ZamowieniePubliczne.numer_bzp"]["page"] == 1
    assert "output" not in meta


def test_api_health_and_document_types():
    assert client.get("/health").json() == {"status": "ok"}
    names = {t["name"] for t in client.get("/document-types").json()}
    assert {"odwolanie", "pelnomocnictwo", "przelew"} <= names


def test_api_rejects_non_pdf():
    response = client.post("/extract", files={"file": ("x.pdf", b"hello", "application/pdf")})
    assert response.status_code == 400


@needs_data
def test_api_extract_returns_uzp_json_and_provenance():
    content = (CASE / "potwierdzenie_przelewu.pdf").read_bytes()
    response = client.post(
        "/extract",
        params={"include_text": "true"},
        files={"file": ("potwierdzenie_przelewu.pdf", content, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "przelew"
    assert body["output"] == json.loads((CASE / "przelew.json").read_text(encoding="utf-8-sig"))
    assert body["fields"]["przelew_bankowy.kwota"]["page"] == 1
    assert body["classification"]["scores"]["przelew"]["score"] > 0
    assert body["pages_text"] and "przelew" in body["pages_text"][0].lower()


@needs_data
def test_api_negative_document_is_empty():
    response = client.post("/extract", files={"file": ("n.pdf", NEGATIVE.read_bytes(), "application/pdf")})
    assert response.json()["document_type"] is None
    assert response.json()["output"] == {}
