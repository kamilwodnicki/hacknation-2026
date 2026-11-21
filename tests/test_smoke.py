from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from src.api.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_powody_dictionary():
    powody = yaml.safe_load((ROOT / "config" / "czynnosc_powody.yaml").read_text(encoding="utf-8"))["powody"]
    assert sorted(powody) == list(range(1, 13))
