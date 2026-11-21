"""Evaluate extraction quality against reference JSON files.

    python -m src.evaluation                         # organizer training set, report to reports/
    python -m src.evaluation --errors 50             # show more mismatches
    python -m src.evaluation --dataset other.yaml --data-dir /path/to/data
"""

import argparse
import os
import sys
from pathlib import Path

from src.config import get_settings
from src.evaluation.report import to_json, to_markdown
from src.evaluation.runner import evaluate, load_dataset
from src.extraction import load_document_types


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(prog="python -m src.evaluation")
    parser.add_argument("--dataset", type=Path, default=settings.config_dir / "evaluation" / "uzp_training.yaml")
    parser.add_argument("--data-dir", type=Path, default=Path(os.getenv("DATA_DIR", "/data")))
    parser.add_argument("--report-dir", type=Path, default=Path("reports"))
    parser.add_argument("--errors", type=int, default=20, help="mismatches listed per document type")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    if not (args.data_dir / dataset.data_dir).exists():
        print(f"Data directory not found: {args.data_dir / dataset.data_dir}", file=sys.stderr)
        return 2

    report = evaluate(dataset, args.data_dir, load_document_types(settings.config_dir / "document_types"))
    markdown = to_markdown(report, max_errors=args.errors)
    print(markdown)

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / f"{dataset.name}.md").write_text(markdown, encoding="utf-8")
    (args.report_dir / f"{dataset.name}.json").write_text(to_json(report), encoding="utf-8")
    print(f"Report saved to {args.report_dir / dataset.name}.md / .json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
