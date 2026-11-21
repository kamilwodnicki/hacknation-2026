"""Response cache and usage meter — protect the API budget.

Every response is stored on disk under a hash of (model, messages, parameters). Running
the same document again (re-evaluation after a code change) costs nothing: only prompts
that were never sent before reach the API.
"""

import hashlib
import json
import threading
from dataclasses import dataclass
from pathlib import Path

from src.llm.client import ChatResponse, LLMClient


@dataclass
class Usage:
    api_calls: int = 0
    cache_hits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def summary(self) -> str:
        return (
            f"wywołania API: {self.api_calls} (z pamięci: {self.cache_hits}), "
            f"tokeny: wejście {self.input_tokens}, wyjście {self.output_tokens}"
        )


USAGE = Usage()
"""Process-wide counter of paid calls (reported by the CLI and the evaluation)."""
_usage_lock = threading.Lock()


class CachedLLM:
    def __init__(self, client: LLMClient, cache_dir: Path):
        self.client = client
        self.cache_dir = cache_dir
        self.description = client.description
        self.model = client.model

    def _key(self, payload: dict) -> str:
        blob = json.dumps({"client": self.description, **payload}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def chat(
        self, messages: list[dict[str, str]], max_tokens: int = 1024, temperature: float = 0.0, json_mode: bool = False
    ) -> ChatResponse:
        key = self._key({"messages": messages, "max_tokens": max_tokens, "temperature": temperature, "json": json_mode})
        path = self.cache_dir / key[:2] / f"{key}.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            with _usage_lock:
                USAGE.cache_hits += 1
            return ChatResponse(
                text=data["text"],
                model=data["model"],
                input_tokens=data.get("input_tokens"),
                output_tokens=data.get("output_tokens"),
                cached=True,
            )

        response = self.client.chat(messages, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode)
        with _usage_lock:
            USAGE.api_calls += 1
            USAGE.input_tokens += response.input_tokens or 0
            USAGE.output_tokens += response.output_tokens or 0
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "text": response.text,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return response
