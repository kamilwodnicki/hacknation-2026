"""Batch processing: every PDF in the input tree -> a JSON file in the output tree.

    input/case1/odwolanie_nr_1.pdf  ->  output/case1/odwolanie_nr_1.json
    (metadata: meta/case1/odwolanie_nr_1.meta.json)

    python -m src process [--input DIR] [--output DIR] [--meta DIR | --no-meta]
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.config import get_settings
from src.llm.cache import USAGE
from src.pipeline import PipelineResult, document_types, effective_mode, process_pdf

log = logging.getLogger("odwolania2json")


def find_pdfs(input_dir: Path) -> list[Path]:
    return sorted(p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf")


def output_path(pdf: Path, input_dir: Path, output_dir: Path, suffix: str = ".json") -> Path:
    """Same relative path and name as the input file, with the extension replaced."""
    relative = pdf.relative_to(input_dir)
    return output_dir / relative.parent / (relative.stem + suffix)


def write_output(path: Path, result: PipelineResult) -> None:
    """UZP JSON; an unrecognized document gives a file containing only `{}` (organizer's rule)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_meta(path: Path, result: PipelineResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = result.model_dump(mode="json", exclude={"output", "pages_text"})
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass
class Summary:
    by_type: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    ocr_documents: int = 0

    def add(self, result: PipelineResult) -> None:
        key = result.document_type or "nierozpoznany"
        self.by_type[key] = self.by_type.get(key, 0) + 1
        if result.error:
            self.errors.append(f"{result.filename}: {result.error}")
        if result.ingestion and result.ingestion.ocr_pages:
            self.ocr_documents += 1


def run(input_dir: Path, output_dir: Path, meta_dir: Path | None) -> Summary:
    pdfs = find_pdfs(input_dir)
    summary = Summary()
    if not pdfs:
        log.warning("Brak plików PDF w %s", input_dir)
        return summary

    document_types()  # validate the configuration before processing anything
    for index, pdf in enumerate(pdfs, start=1):
        relative = pdf.relative_to(input_dir)
        result = process_pdf(pdf, filename=str(relative))
        write_output(output_path(pdf, input_dir, output_dir), result)
        if meta_dir is not None:
            write_meta(output_path(pdf, input_dir, meta_dir, ".meta.json"), result)
        summary.add(result)

        found = sum(1 for t in result.fields.values() if t.value is not None)
        ocr = f", OCR str. {result.ingestion.ocr_pages}" if result.ingestion and result.ingestion.ocr_pages else ""
        status = result.error or f"{result.document_type or 'nierozpoznany (pusty JSON)'}, pola: {found}/{len(result.fields)}{ocr}"
        print(f"[{index}/{len(pdfs)}] {relative} -> {status} ({result.seconds:.1f} s)", flush=True)
    return summary


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(prog="python -m src", description="Odwołania2json — PDF -> JSON (UZP)")
    sub = parser.add_subparsers(dest="command")
    process = sub.add_parser("process", help="przetwórz wszystkie PDF-y z katalogu wejściowego")
    process.add_argument("--input", type=Path, default=settings.input_dir)
    process.add_argument("--output", type=Path, default=settings.output_dir)
    process.add_argument("--meta", type=Path, default=settings.meta_dir)
    process.add_argument("--no-meta", action="store_true", help="nie zapisuj metadanych ekstrakcji")
    args = parser.parse_args(argv)
    if args.command is None:
        args = parser.parse_args(["process", *(argv or [])])

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    if not args.input.is_dir():
        print(f"Katalog wejściowy nie istnieje: {args.input}", file=sys.stderr)
        return 2

    start = time.perf_counter()
    meta_dir = None if args.no_meta or not settings.write_meta else args.meta
    summary = run(args.input, args.output, meta_dir)

    total = sum(summary.by_type.values())
    print(f"\nGotowe: {total} plików w {time.perf_counter() - start:.1f} s -> {args.output}")
    for name, count in sorted(summary.by_type.items()):
        print(f"  {name}: {count}")
    if summary.ocr_documents:
        print(f"  w tym ze skanem (OCR): {summary.ocr_documents}")
    if meta_dir is not None and total:
        print(f"Metadane ekstrakcji: {meta_dir}")
    print(f"Tryb ekstrakcji: {effective_mode(settings)}" + (f" · LLM: {USAGE.summary()}" if USAGE.api_calls or USAGE.cache_hits else ""))
    for error in summary.errors:
        print(f"BŁĄD {error}", file=sys.stderr)
    return 1 if summary.errors else 0


if __name__ == "__main__":
    sys.exit(main())
