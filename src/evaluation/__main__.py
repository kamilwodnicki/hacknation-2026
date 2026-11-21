"""Evaluate extraction quality against reference JSON files.

    python -m src.evaluation                         # rules only (free), report to reports/
    python -m src.evaluation --errors 50             # show more mismatches
    python -m src.evaluation --dataset other.yaml --data-dir /path/to/data

With the language model (costs money — the tools container has LLM off by default):
    docker compose run --rm -e LLM_PROVIDER=openai tests python -m src.evaluation --mode hybrid --estimate
    docker compose run --rm -e LLM_PROVIDER=openai tests python -m src.evaluation --mode hybrid --limit 3
Responses are cached in cache/llm, so re-running the same documents is free.
"""

import argparse
import os
import sys
from pathlib import Path

from src.config import get_settings
from src.evaluation.report import to_json, to_markdown
from src.evaluation.runner import estimate_llm, evaluate, load_dataset
from src.extraction import load_document_types
from src.llm.cache import USAGE
from src.pipeline import llm_client


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(prog="python -m src.evaluation")
    parser.add_argument("--dataset", type=Path, default=settings.config_dir / "evaluation" / "uzp_training.yaml")
    parser.add_argument("--data-dir", type=Path, default=Path(os.getenv("DATA_DIR", "/data")))
    parser.add_argument("--report-dir", type=Path, default=Path("reports"))
    parser.add_argument("--errors", type=int, default=20, help="mismatches listed per document type")
    parser.add_argument("--oracle", action="store_true", help="extract with the expected type (skip classifier)")
    parser.add_argument("--mode", choices=["rules", "llm", "hybrid"], default="rules", help="default: rules (free)")
    parser.add_argument("--limit", type=int, help="only the first N cases (cheap LLM trials)")
    parser.add_argument("--cases", nargs="+", help="only these case directories, e.g. przyklad_49")
    parser.add_argument("--estimate", action="store_true", help="estimate LLM tokens without calling the API")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    if not (args.data_dir / dataset.data_dir).exists():
        print(f"Data directory not found: {args.data_dir / dataset.data_dir}", file=sys.stderr)
        return 2
    types = load_document_types(settings.config_dir / "document_types")

    if args.mode != "rules":
        client = llm_client(settings)
        if client is None:
            print("LLM nie jest skonfigurowany (LLM_PROVIDER / klucz) — uruchom z -e LLM_PROVIDER=openai", file=sys.stderr)
            return 2
        print(f"LLM: {client.description} · tryb {args.mode}")

    if args.estimate:
        e = estimate_llm(dataset, args.data_dir, types, args.mode, settings.llm_max_chars, args.limit, args.cases)
        print(
            f"Szacunek (bez wywołań API): dokumentów {e['documents']}, do modelu trafiłoby {e['sent']}, "
            f"~{e['input_tokens']} tokenów wejścia + ~{e['output_tokens']} wyjścia "
            "(dokumenty już w pamięci podręcznej nie kosztują ponownie)."
        )
        return 0

    report = evaluate(dataset, args.data_dir, types, oracle=args.oracle, mode=args.mode, limit=args.limit, only=args.cases)
    markdown = to_markdown(report, max_errors=args.errors)
    print(markdown)
    if args.mode != "rules":
        print(f"Zużycie LLM w tym przebiegu: {USAGE.summary()}")

    suffix = "" if args.mode == "rules" and not (args.limit or args.cases) else f"_{args.mode}" + ("_partial" if args.limit or args.cases else "")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / f"{dataset.name}{suffix}.md").write_text(markdown, encoding="utf-8")
    (args.report_dir / f"{dataset.name}{suffix}.json").write_text(to_json(report), encoding="utf-8")
    print(f"Report saved to {args.report_dir / dataset.name}{suffix}.md / .json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
