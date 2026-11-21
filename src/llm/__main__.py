"""Check the LLM connection.

    python -m src.llm ping      # one short request: provider, model, answer, tokens
    python -m src.llm models    # model IDs available at an OpenAI-compatible provider
"""

import argparse
import sys

from src.llm import LLMError, get_llm_client

PING_PROMPT = (
    "Odpowiedz jednym zdaniem po polsku: jak brzmi mianownik imienia i nazwiska "
    "z frazy 'udzielam pełnomocnictwa Janowi Kowalskiemu'?"
)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m src.llm")
    parser.add_argument("command", choices=["ping", "models"])
    args = parser.parse_args()

    try:
        client = get_llm_client()
    except LLMError as exc:
        print(f"[BŁĄD konfiguracji] {exc}", file=sys.stderr)
        return 2
    if client is None:
        print("LLM wyłączony (LLM_PROVIDER=none) — aplikacja działa na samych regułach.")
        return 0

    print(f"Dostawca: {client.description}")
    try:
        if args.command == "models":
            if not hasattr(client, "list_models"):
                print("Lista modeli dostępna tylko dla API zgodnego z OpenAI.")
                return 0
            for model_id in client.list_models():
                print(f"  {model_id}")
            return 0
        response = client.chat([{"role": "user", "content": PING_PROMPT}], max_tokens=60)
    except LLMError as exc:
        print(f"[BŁĄD wywołania] {exc}", file=sys.stderr)
        return 1
    print(f"Model:     {response.model}")
    print(f"Odpowiedź: {response.text.strip()}")
    print(f"Tokeny:    wejście {response.input_tokens}, wyjście {response.output_tokens} · czas {response.seconds:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
