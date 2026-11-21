"""Settings file selection: .env.overdrive replaces .env completely."""

from src.config import get_settings, settings_file


def make(tmp_path, monkeypatch, **files):
    for name, content in files.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    monkeypatch.setenv("PISMO_ENV_DIR", str(tmp_path))
    monkeypatch.delenv("LLM_MODEL_NAME", raising=False)
    monkeypatch.delenv("OCR_DPI", raising=False)
    get_settings.cache_clear()


def test_overdrive_wins_and_env_is_ignored_completely(tmp_path, monkeypatch):
    make(tmp_path, monkeypatch, **{".env": "LLM_MODEL_NAME=z-env\nOCR_DPI=111\n", ".env.overdrive": "LLM_MODEL_NAME=z-overdrive\n"})
    try:
        assert settings_file().name == ".env.overdrive"
        s = get_settings()
        assert s.llm_model_name == "z-overdrive"
        assert s.ocr_dpi == 200  # value only in .env is NOT used (default instead)
    finally:
        get_settings.cache_clear()


def test_env_used_when_no_overdrive(tmp_path, monkeypatch):
    make(tmp_path, monkeypatch, **{".env": "LLM_MODEL_NAME=z-env\n"})
    try:
        assert settings_file().name == ".env"
        assert get_settings().llm_model_name == "z-env"
    finally:
        get_settings.cache_clear()


def test_defaults_use_ai_with_mistral_eu(tmp_path, monkeypatch):
    make(tmp_path, monkeypatch)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    try:
        s = get_settings()
        assert (s.llm_provider, s.extraction_mode) == ("openai", "hybrid")
        assert s.llm_api_base_url == "https://api.eu.mistral.ai/v1"
        assert s.llm_model_name == "ministral-14b-2512"
    finally:
        get_settings.cache_clear()
