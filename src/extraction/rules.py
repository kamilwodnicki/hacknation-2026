"""Rule strategies that locate a field value in document text.

Every candidate carries its origin (page, line, matched text) so the UI can show where
each value came from (transparency of extraction).
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from src.extraction.schema import LabelStrategy, MatchesSplit, NthMatchStrategy, RegexStrategy, SectionSplit
from src.ingestion import IngestedDocument, PageSource
from src.validation.normalizers import VALUE_TYPES

# Separators allowed between a label and its value: spaces, colon, dot leaders, dashes.
_LABEL_TAIL = r"[\s:.\-–…]*"


@dataclass(frozen=True)
class Line:
    page: int
    text: str


@dataclass(frozen=True)
class Candidate:
    raw: str
    page: int
    snippet: str
    """The line(s) the value was taken from."""
    detail: str
    """Human readable description of the rule that matched, e.g. `label "Data operacji"`."""


def document_lines(doc: IngestedDocument) -> list[Line]:
    return [
        Line(page.number, line)
        for page in doc.pages
        if page.source != PageSource.SKIPPED
        for line in page.text.split("\n")
        if line.strip()
    ]


def _case_variants(label: str) -> set[str]:
    """Labels are matched as written, Capitalized, Title Case or UPPER CASE — but not in
    lower case, so a label word inside a value ("opłata skarbowa") is not taken for a
    label ("Opłata: 0,00 PLN")."""
    return {label, label[:1].upper() + label[1:], label.title(), label.upper()}


def compile_labels(labels: list[str]) -> re.Pattern[str]:
    """Match any label at the start of a line, of a column (after 2+ spaces) or of an
    enumeration item ("KRS: 1, NIP: 2", "(KRS 1 · NIP 2)").

    Longer labels are tried first so "Tytuł przelewu" wins over "Tytuł".
    """
    variants = {v for label in labels for v in _case_variants(label)}
    alternatives = "|".join(
        r"\s+".join(map(re.escape, label.split())) for label in sorted(variants, key=len, reverse=True)
    )
    return re.compile(
        rf"(?:^|(?<=\s\s)|(?<=[,;·|•(])\s*)[^\w\s]*(?P<label>{alternatives})(?=[\s:.\-–…]|$){_LABEL_TAIL}(?P<rest>.*)$"
    )


def _find_typed(text: str, value_type: str) -> str | None:
    m = re.search(VALUE_TYPES[value_type].pattern, text, re.IGNORECASE)
    return m.group(0) if m else None


def run_label(
    strategy: LabelStrategy,
    lines: list[Line],
    value_type: str,
    stop: re.Pattern[str] | None,
) -> Iterator[Candidate]:
    label_re = compile_labels(strategy.labels)
    for i, line in enumerate(lines):
        m = label_re.search(line.text)
        if not m:
            continue
        label, rest = m.group("label"), m.group("rest").strip()
        detail = f'label "{label}"'

        if strategy.multiline:
            following = lines[i + 1 : i + 1 + strategy.max_lines]
            parts = [rest] if rest else []
            for k, nxt in enumerate(following):
                # The first value line under an empty label is always part of the value.
                if (k > 0 or rest) and stop and stop.search(nxt.text):
                    break
                parts.append(nxt.text.strip())
            if parts:
                snippet = "\n".join([line.text, *(p.text for p in following[: len(parts) - bool(rest)])])
                yield Candidate(" ".join(parts), line.page, snippet, detail)
            continue

        if value_type == "text":
            if rest:
                yield Candidate(rest, line.page, line.text, detail)
            continue

        window = [line]
        for nxt in lines[i + 1 : i + 1 + strategy.lookahead]:
            if stop and stop.search(nxt.text):
                break
            window.append(nxt)
        texts = [rest] + [w.text for w in window[1:]]
        for j, text in enumerate(texts):
            if raw := _find_typed(text, value_type):
                yield Candidate(raw, window[j].page, window[j].text, detail)
                break
        else:
            # Value broken across lines, e.g. an account number wrapped by the layout.
            joined = " ".join(texts)
            if raw := _find_typed(joined, value_type):
                yield Candidate(raw, line.page, "\n".join(w.text for w in window), detail + " (joined lines)")


def run_regex(strategy: RegexStrategy, lines: list[Line], value_type: str) -> Iterator[Candidate]:
    """Run over whole pages, so `\\s` in the pattern may span line breaks.

    `{value}` in the pattern is replaced with the field type's own value pattern, e.g.
    'w dniu\\s+({value})' for a date written inside a sentence.
    """
    flags = 0
    for name in strategy.flags:
        flags |= getattr(re, name)
    pattern = re.compile(strategy.pattern.replace("{value}", f"(?:{VALUE_TYPES[value_type].pattern})"), flags)
    for page, text in _page_texts(lines).items():
        for m in pattern.finditer(text):
            start = text.rfind("\n", 0, m.start()) + 1
            end = text.find("\n", m.end())
            snippet = text[start : end if end != -1 else len(text)]
            yield Candidate(m.group(1) if m.groups() else m.group(0), page, snippet, "regex")


@dataclass(frozen=True)
class ItemText:
    """Text region of one list item."""

    lines: list[Line]
    presets: dict[str, str]
    """Raw values from named regex groups (field name -> text)."""
    detail: str


def _page_texts(lines: list[Line]) -> dict[int, str]:
    pages: dict[int, list[str]] = {}
    for line in lines:
        pages.setdefault(line.page, []).append(line.text)
    return {page: "\n".join(texts) for page, texts in pages.items()}


def split_sections(split: SectionSplit, lines: list[Line]) -> list[ItemText]:
    start_re = compile_labels(split.start)
    end_re = compile_labels(split.end) if split.end else None
    marker_re = re.compile(split.item_marker) if split.item_marker else None
    items: list[ItemText] = []
    i = 0
    while i < len(lines):
        m = start_re.search(lines[i].text)
        if not m:
            i += 1
            continue
        label = m.group("label")
        region = [Line(lines[i].page, m.group("rest"))] if m.group("rest").strip() else []
        j = i + 1
        while j < len(lines) and j - i <= split.max_lines:
            if start_re.search(lines[j].text) or (end_re and end_re.search(lines[j].text)):
                break
            region.append(lines[j])
            j += 1
        i = j

        if marker_re and any(marker_re.search(line.text) for line in region):
            current: list[Line] | None = None
            for line in region:
                if marker_re.search(line.text):
                    current = [line]
                    items.append(ItemText(current, {}, f'section "{label}", item {len(items) + 1}'))
                elif current is not None:
                    current.append(line)
        elif region:
            items.append(ItemText(region, {}, f'section "{label}"'))
    return items


def split_matches(split: MatchesSplit, lines: list[Line]) -> list[ItemText]:
    flags = 0
    for name in split.flags:
        flags |= getattr(re, name)
    pattern = re.compile(split.pattern, flags)
    items = []
    for page, text in _page_texts(lines).items():
        for m in pattern.finditer(text):
            presets = {k: v for k, v in m.groupdict().items() if v is not None}
            items.append(ItemText([Line(page, m.group(0))], presets, "pattern match"))
    return items


def run_nth_match(strategy: NthMatchStrategy, lines: list[Line], value_type: str) -> Iterator[Candidate]:
    """n-th distinct valid value of the type, in reading order."""
    pattern = re.compile(VALUE_TYPES[value_type].pattern, re.IGNORECASE)
    normalize = VALUE_TYPES[value_type].normalize
    seen: list[object] = []
    for line in lines:
        for m in pattern.finditer(line.text):
            value = normalize(m.group(0))
            if value is None or value in seen:
                continue
            seen.append(value)
            if len(seen) == strategy.n:
                yield Candidate(m.group(0), line.page, line.text, f"occurrence #{strategy.n} of {value_type}")
                return
