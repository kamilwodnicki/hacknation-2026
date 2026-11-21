"""Render an EvaluationReport as Markdown (console + file) and JSON."""

import json
from datetime import datetime

from src.evaluation.metrics import Counts
from src.evaluation.runner import EvaluationReport


def _row(name: str, uzp: Counts, exact: Counts) -> str:
    return (
        f"| {name} | {uzp.tp} | {uzp.fp} | {uzp.fn} | {uzp.precision:.3f} | "
        f"{uzp.recall:.3f} | **{uzp.f1:.3f}** | {exact.f1:.3f} |"
    )


_HEADER = "| | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |\n|---|---|---|---|---|---|---|---|"


def to_markdown(report: EvaluationReport, max_errors: int = 20) -> str:
    total_u, total_e = report.total("uzp"), report.total("exact")
    lines = [
        f"# Ewaluacja: {report.dataset}",
        "",
        f"Wygenerowano: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "Metryka: F1 na poziomie pól (wartości `null` nie są liczone; błędna wartość = FP + FN; "
        "listy dopasowywane po treści).",
        "",
        "**F1 (UZP)** — zasada organizatora: pola typu „długi string” (nazwy firm, tytuły) zaliczane przy "
        "podobieństwie ≥ 80%, pozostałe muszą być identyczne. **F1 (dokładne)** — wszystkie pola identyczne.",
        "",
        "Typ dokumentu do ekstrakcji: "
        + ("**oczekiwany (oracle)** — klasyfikator pominięty." if report.oracle else "**z klasyfikatora** (pełny pipeline)."),
        "",
        f"Tryb ekstrakcji: **{report.mode}**"
        + (
            f" — do modelu wysłano {report.llm.documents_sent} dok. (z pamięci podręcznej: {report.llm.cached}), "
            f"pominięto {report.llm.skipped} (reguły kompletne), błędy LLM: {report.llm.errors}; "
            f"nowe tokeny: wejście {report.llm.input_tokens}, wyjście {report.llm.output_tokens}."
            if report.mode != "rules"
            else "."
        ),
        "",
        "## Podsumowanie",
        "",
        _HEADER,
        _row("**RAZEM**", total_u, total_e),
    ]
    for name, t in sorted(report.types.items()):
        label = f"{name} ({t.documents} dok.)" + ("" if t.defined else " — brak pól w YAML")
        lines.append(_row(label, t.total("uzp"), t.total("exact")))

    if report.classifications:
        none = "∅ (nierozpoznany)"
        labels = sorted({x for pair in report.confusion() for x in pair}, key=lambda x: (x is None, x or ""))
        lines += [
            "",
            "## Klasyfikacja",
            "",
            f"Trafność: **{report.classification_accuracy:.3f}** "
            f"({sum(c.expected == c.predicted for c in report.classifications)}/{len(report.classifications)})",
            "",
            "| oczekiwany \\ przewidziany | " + " | ".join(x or none for x in labels) + " |",
            "|---|" + "---|" * len(labels),
        ]
        for expected in labels:
            cells = [str(report.confusion()[(expected, predicted)]) for predicted in labels]
            lines.append(f"| {expected or none} | " + " | ".join(cells) + " |")
        wrong = [c for c in report.classifications if c.expected != c.predicted]
        if wrong:
            lines += ["", "Błędne klasyfikacje:", ""]
            lines += [f"- `{c.document}`: oczekiwano {c.expected}, otrzymano {c.predicted} ({c.reason})" for c in wrong]

    for name, t in sorted(report.types.items()):
        lines += ["", f"## {name}", "", _HEADER.replace("| |", "| Pole |", 1)]
        for path in sorted(t.exact):
            lines.append(_row(f"`{path}`", t.uzp[path], t.exact[path]))
        if t.errors and max_errors:
            lines += ["", f"Przykładowe różnice dokładne ({min(max_errors, len(t.errors))} z {len(t.errors)}):", ""]
            for case, m in t.errors[:max_errors]:
                expected = json.dumps(m.expected, ensure_ascii=False)
                predicted = json.dumps(m.predicted, ensure_ascii=False)
                lines.append(f"- `{case}` `{m.path}`: oczekiwano {expected}, otrzymano {predicted}")

    if report.missing_files:
        lines += ["", "## Brakujące pliki", "", *(f"- {f}" for f in report.missing_files)]
    return "\n".join(lines) + "\n"


def to_json(report: EvaluationReport) -> str:
    def counts(c: Counts) -> dict:
        return {"tp": c.tp, "fp": c.fp, "fn": c.fn, "precision": c.precision, "recall": c.recall, "f1": c.f1}

    data = {
        "dataset": report.dataset,
        "oracle": report.oracle,
        "classification": {
            "accuracy": report.classification_accuracy,
            "documents": [c.__dict__ for c in report.classifications],
        },
        "total": {"uzp": counts(report.total("uzp")), "exact": counts(report.total("exact"))},
        "types": {
            name: {
                "documents": t.documents,
                "defined": t.defined,
                "uzp": counts(t.total("uzp")),
                "exact": counts(t.total("exact")),
                "fields": {p: {"uzp": counts(t.uzp[p]), "exact": counts(t.exact[p])} for p in sorted(t.exact)},
            }
            for name, t in sorted(report.types.items())
        },
        "missing_files": report.missing_files,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
