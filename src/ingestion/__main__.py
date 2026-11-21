"""Inspect ingestion output.

    python -m src.ingestion FILE.pdf [--text] [--json]
    python -m src.ingestion DIRECTORY            # summary for every PDF (recursive)
"""

import argparse
import json
import sys
import time
from pathlib import Path

from src.ingestion import IngestionError, read_pdf


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m src.ingestion")
    parser.add_argument("path", type=Path)
    parser.add_argument("--text", action="store_true", help="print extracted text")
    parser.add_argument("--json", action="store_true", help="print the full IngestedDocument as JSON")
    args = parser.parse_args()

    files = sorted(args.path.rglob("*.pdf")) if args.path.is_dir() else [args.path]
    failed = 0
    for f in files:
        start = time.perf_counter()
        try:
            doc = read_pdf(f)
        except IngestionError as exc:
            failed += 1
            print(f"ERROR {exc}", file=sys.stderr)
            continue
        elapsed = time.perf_counter() - start
        name = f.relative_to(args.path) if args.path.is_dir() else f.name
        chars = sum(len(p.text) for p in doc.pages)
        conf = [p.ocr_confidence for p in doc.pages if p.ocr_confidence is not None]
        conf_s = f" ocr_conf={min(conf):.2f}" if conf else ""
        print(f"{name}  pages={doc.page_count} ocr={doc.ocr_pages or '-'} chars={chars}{conf_s} {elapsed:.1f}s")
        if args.json:
            print(json.dumps(doc.model_dump(mode="json"), ensure_ascii=False, indent=2))
        elif args.text:
            print(doc.full_text())
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
