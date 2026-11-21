"""Chat clients for the supported LLM providers.

* VertexMistralClient — Google Cloud Vertex AI (Gemini Enterprise Agent Platform), partner
  model Mistral called through `:rawPredict` (Mistral chat format), authenticated with a
  service-account key file (short-lived OAuth tokens refreshed automatically).
* OpenAICompatibleClient — any OpenAI-compatible endpoint (OVHcloud, Scaleway, Mistral EU).

Secrets are never logged: only the provider, project ID, region and model are reported.
"""

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import requests

from src.config import Settings, get_settings


class LLMError(Exception):
    """The LLM call failed (configuration, authentication, quota, network or response)."""


@dataclass
class ChatResponse:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    seconds: float = 0.0
    cached: bool = False
    """True = served from the on-disk response cache (no API call, no cost)."""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


class LLMClient(Protocol):
    description: str
    """Human-readable provider/model/region (no secrets)."""

    model: str

    def chat(
        self, messages: list[dict[str, str]], max_tokens: int = 1024, temperature: float = 0.0, json_mode: bool = False
    ) -> ChatResponse: ...


class VertexMistralClient:
    _SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

    def __init__(self, settings: Settings):
        from google.oauth2 import service_account

        key_file = Path(settings.google_application_credentials)
        if not key_file.is_file():
            raise LLMError(f"brak pliku klucza konta usługi: {key_file}")
        try:
            self._credentials = service_account.Credentials.from_service_account_file(str(key_file), scopes=self._SCOPES)
        except (ValueError, KeyError) as exc:
            raise LLMError(f"nieprawidłowy plik klucza konta usługi ({key_file.name}): {exc}") from exc

        self.project = settings.vertex_project or self._credentials.project_id
        if not self.project:
            raise LLMError("brak ID projektu (VERTEX_PROJECT ani project_id w pliku klucza)")
        self.region = settings.vertex_region
        self.model = settings.vertex_model
        self.timeout = settings.llm_timeout
        self.url = (
            f"https://{self.region}-aiplatform.googleapis.com/v1/projects/{self.project}/locations/{self.region}"
            f"/publishers/{settings.vertex_publisher}/models/{self.model}:rawPredict"
        )
        self.description = f"Vertex AI · {settings.vertex_publisher}/{self.model} · projekt {self.project} · region {self.region}"
        self._lock = threading.Lock()

    def _token(self) -> str:
        from google.auth.transport.requests import Request

        with self._lock:
            if not self._credentials.valid:
                try:
                    self._credentials.refresh(Request())
                except Exception as exc:  # google.auth.exceptions.RefreshError and transport errors
                    raise LLMError(f"nie udało się uzyskać tokenu Google: {exc}") from exc
            return self._credentials.token

    def chat(
        self, messages: list[dict[str, str]], max_tokens: int = 1024, temperature: float = 0.0, json_mode: bool = False
    ) -> ChatResponse:
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature, "stream": False}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        start = time.perf_counter()
        try:
            response = requests.post(
                self.url,
                headers={"Authorization": f"Bearer {self._token()}", "Content-Type": "application/json; charset=utf-8"},
                data=json.dumps(body),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise LLMError(f"błąd połączenia z Vertex AI: {exc}") from exc
        if response.status_code != 200:
            raise LLMError(f"Vertex AI zwrócił {response.status_code}: {response.text[:500]}")
        return _parse_chat_completion(response.json(), self.model, time.perf_counter() - start)


class OpenAICompatibleClient:
    _PLACEHOLDER_KEYS = ("changeme", "wklej_tutaj")

    def __init__(self, settings: Settings):
        if not settings.llm_api_base_url or not settings.llm_api_key or not settings.llm_model_name:
            raise LLMError("brak LLM_API_BASE_URL / LLM_API_KEY / LLM_MODEL_NAME")
        if settings.llm_api_key.lower().startswith(self._PLACEHOLDER_KEYS):
            raise LLMError("LLM_API_KEY w .env to wciąż wartość przykładowa — wklej swój klucz API")
        from openai import OpenAI

        self._client = OpenAI(base_url=settings.llm_api_base_url, api_key=settings.llm_api_key, timeout=settings.llm_timeout)
        self.model = settings.llm_model_name
        self.description = f"API zgodne z OpenAI · {self.model} · {settings.llm_api_base_url}"

    def chat(
        self, messages: list[dict[str, str]], max_tokens: int = 1024, temperature: float = 0.0, json_mode: bool = False
    ) -> ChatResponse:
        start = time.perf_counter()
        extra = {"response_format": {"type": "json_object"}} if json_mode else {}
        try:
            completion = self._client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=max_tokens, temperature=temperature, **extra
            )
        except Exception as exc:  # openai.APIError and transport errors
            raise LLMError(f"błąd API: {exc}") from exc
        return _parse_chat_completion(completion.model_dump(), self.model, time.perf_counter() - start)

    def list_models(self) -> list[str]:
        try:
            return sorted(m.id for m in self._client.models.list())
        except Exception as exc:
            raise LLMError(f"błąd API: {exc}") from exc


def _parse_chat_completion(data: dict[str, Any], model: str, seconds: float) -> ChatResponse:
    try:
        text = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"nieoczekiwany format odpowiedzi: {str(data)[:300]}") from exc
    usage = data.get("usage") or {}
    return ChatResponse(
        text=text,
        model=data.get("model") or model,
        input_tokens=usage.get("prompt_tokens"),
        output_tokens=usage.get("completion_tokens"),
        seconds=round(seconds, 2),
        raw=data,
    )


def get_llm_client(settings: Settings | None = None) -> LLMClient | None:
    """The configured client, or None when LLM_PROVIDER=none. Raises LLMError when the
    provider is selected but cannot be configured (e.g. missing key file)."""
    s = settings or get_settings()
    if s.llm_provider == "vertex":
        return VertexMistralClient(s)
    if s.llm_provider == "openai":
        return OpenAICompatibleClient(s)
    return None
