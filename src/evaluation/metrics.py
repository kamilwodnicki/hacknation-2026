"""Field-level precision / recall / F1 between predicted and reference JSON.

The organizer does not define the exact F1 procedure, so we use the standard
field-level variant:
  * every leaf value is one item, identified by its path ('a.b', lists as 'a[].b'),
  * null values are "no answer" and are not counted,
  * TP — predicted value equal to the reference value,
  * FP — predicted value that is not in the reference (a wrong value is FP + FN),
  * FN — reference value that was not predicted.
Lists are compared as multisets per path, so item order does not matter.

Two comparison modes are reported:
  * strict  — exact values (numbers compared numerically, 200 == 200.0),
  * lenient — strings case-folded with collapsed whitespace and trimmed punctuation.
"""

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def __iadd__(self, other: "Counts") -> "Counts":
        self.tp += other.tp
        self.fp += other.fp
        self.fn += other.fn
        return self

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


@dataclass
class Mismatch:
    path: str
    expected: list[Any]
    predicted: list[Any]


@dataclass
class Comparison:
    strict: dict[str, Counts] = field(default_factory=dict)
    lenient: dict[str, Counts] = field(default_factory=dict)
    mismatches: list[Mismatch] = field(default_factory=list)
    """Paths with a strict mismatch (for error analysis)."""


def flatten(obj: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from flatten(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(obj, list):
        for item in obj:
            yield from flatten(item, f"{prefix}[]")
    else:
        yield prefix, obj


def canonical(value: Any, lenient: bool) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        number = float(value)
        return str(int(number)) if number.is_integer() else repr(round(number, 6))
    text = str(value)
    if lenient:
        text = re.sub(r"\s+", " ", text).strip(" \t.,;:„”\"'").casefold()
    return text or None


def _values_by_path(obj: Any, lenient: bool) -> dict[str, Counter[str]]:
    out: dict[str, Counter[str]] = {}
    for path, value in flatten(obj):
        bucket = out.setdefault(path, Counter())
        if (canon := canonical(value, lenient)) is not None:
            bucket[canon] += 1
    return out


def _score(predicted: Any, reference: Any, lenient: bool) -> dict[str, Counts]:
    pred = _values_by_path(predicted, lenient)
    ref = _values_by_path(reference, lenient)
    result: dict[str, Counts] = {}
    for path in ref.keys() | pred.keys():
        p, r = pred.get(path, Counter()), ref.get(path, Counter())
        tp = sum((p & r).values())
        result[path] = Counts(tp=tp, fp=sum(p.values()) - tp, fn=sum(r.values()) - tp)
    return result


def compare(predicted: Any, reference: Any) -> Comparison:
    strict = _score(predicted, reference, lenient=False)
    comparison = Comparison(strict=strict, lenient=_score(predicted, reference, lenient=True))
    raw_pred: dict[str, list[Any]] = {}
    raw_ref: dict[str, list[Any]] = {}
    for path, value in flatten(predicted):
        raw_pred.setdefault(path, []).append(value)
    for path, value in flatten(reference):
        raw_ref.setdefault(path, []).append(value)
    for path, counts in sorted(strict.items()):
        if counts.fp or counts.fn:
            comparison.mismatches.append(Mismatch(path, raw_ref.get(path, []), raw_pred.get(path, [])))
    return comparison
