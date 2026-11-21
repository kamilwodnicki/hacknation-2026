"""Field-level precision / recall / F1 between predicted and reference JSON.

Field-level counting (as announced by the organizer):
  * every leaf value is one item, identified by its path ('a.b', lists as 'a[].b'),
  * null values are "no answer" and are not counted,
  * TP — predicted value matching a reference value,
  * FP — predicted value with no match in the reference (a wrong value is FP + FN),
  * FN — reference value that was not predicted.
Lists are matched by content (not by position): values of the same path are paired.

Two comparison modes are reported:
  * exact — every value must be identical (numbers compared numerically, 200 == 200.0),
  * uzp   — the organizer's rule: "long string" fields (company names, titles) match when
            their similarity is >= the threshold (80%); all other fields must be identical.
            The long-string paths are configured in the evaluation dataset YAML.
"""

from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from difflib import SequenceMatcher
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
    exact: dict[str, Counts] = field(default_factory=dict)
    uzp: dict[str, Counts] = field(default_factory=dict)
    mismatches: list[Mismatch] = field(default_factory=list)
    """Paths with an exact-mode mismatch (for error analysis)."""


def flatten(obj: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from flatten(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(obj, list):
        for item in obj:
            yield from flatten(item, f"{prefix}[]")
    else:
        yield prefix, obj


def canonical(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        number = float(value)
        return str(int(number)) if number.is_integer() else repr(round(number, 6))
    return str(value) or None


def similarity(a: str, b: str) -> float:
    """Similarity in [0, 1] (difflib ratio: 2 * matching characters / total length)."""
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _values_by_path(obj: Any) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path, value in flatten(obj):
        bucket = out.setdefault(path, [])
        if (canon := canonical(value)) is not None:
            bucket.append(canon)
    return out


def _match_exact(pred: list[str], ref: list[str]) -> int:
    return sum((Counter(pred) & Counter(ref)).values())


def _match_fuzzy(pred: list[str], ref: list[str], threshold: float) -> int:
    """Greedy content matching: best-scoring pairs first, each value used once."""
    pairs = sorted(
        ((similarity(p, r), i, j) for i, p in enumerate(pred) for j, r in enumerate(ref)),
        reverse=True,
    )
    used_pred: set[int] = set()
    used_ref: set[int] = set()
    for score, i, j in pairs:
        if score < threshold:
            break
        if i not in used_pred and j not in used_ref:
            used_pred.add(i)
            used_ref.add(j)
    return len(used_pred)


def _score(
    pred: dict[str, list[str]], ref: dict[str, list[str]], fuzzy: dict[str, float]
) -> dict[str, Counts]:
    result: dict[str, Counts] = {}
    for path in ref.keys() | pred.keys():
        p, r = pred.get(path, []), ref.get(path, [])
        tp = _match_fuzzy(p, r, fuzzy[path]) if path in fuzzy else _match_exact(p, r)
        result[path] = Counts(tp=tp, fp=len(p) - tp, fn=len(r) - tp)
    return result


def _digits(values: dict[str, list[str]], paths: set[str]) -> dict[str, list[str]]:
    return {p: ["".join(ch for ch in v if ch.isdigit()) if p in paths else v for v in vs] for p, vs in values.items()}


def compare(
    predicted: Any,
    reference: Any,
    fuzzy_fields: dict[str, float] | None = None,
    digits_only: set[str] | None = None,
) -> Comparison:
    """`fuzzy_fields`: path ('a[].b') -> similarity threshold for the uzp mode.
    `digits_only`: paths compared by their digits only in the uzp mode (e.g. an account number
    with / without the "PL" prefix, where the reference files are inconsistent)."""
    pred, ref = _values_by_path(predicted), _values_by_path(reference)
    uzp_pred, uzp_ref = (_digits(pred, digits_only), _digits(ref, digits_only)) if digits_only else (pred, ref)
    comparison = Comparison(exact=_score(pred, ref, {}), uzp=_score(uzp_pred, uzp_ref, fuzzy_fields or {}))

    raw_pred: dict[str, list[Any]] = {}
    raw_ref: dict[str, list[Any]] = {}
    for path, value in flatten(predicted):
        raw_pred.setdefault(path, []).append(value)
    for path, value in flatten(reference):
        raw_ref.setdefault(path, []).append(value)
    for path, counts in sorted(comparison.exact.items()):
        if counts.fp or counts.fn:
            comparison.mismatches.append(Mismatch(path, raw_ref.get(path, []), raw_pred.get(path, [])))
    return comparison
