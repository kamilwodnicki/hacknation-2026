"""Schema of document-type configuration files (config/document_types/*.yaml).

A document type is described entirely in YAML:
  * `classification` — signals used to recognize the type,
  * `output` — the exact JSON structure to produce; every leaf is a field spec (has `type`),
  * `stop_labels` — labels that end a multi-line value (besides labels of other fields).

Loading validates the YAML, so configuration errors are reported at startup.
"""

import re
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.validation.checksums import CHECKSUMS
from src.validation.normalizers import VALUE_TYPES


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LabelStrategy(_Strict):
    """Value written after a label: on the same line or within the next `lookahead` lines."""

    method: Literal["label"]
    labels: list[str] = Field(min_length=1)
    lookahead: int = 2
    multiline: bool = False
    """Collect the value across lines until the next label / stop label (e.g. a transfer title)."""
    max_lines: int = 6


class RegexStrategy(_Strict):
    """Custom regular expression; the first capture group (or the whole match) is the value."""

    method: Literal["regex"]
    pattern: str
    flags: list[Literal["IGNORECASE", "MULTILINE", "DOTALL"]] = ["IGNORECASE"]

    @field_validator("pattern")
    @classmethod
    def _compiles(cls, v: str) -> str:
        _check_regex(v.replace("{value}", "x"), "pattern")
        return v


class NthMatchStrategy(_Strict):
    """The n-th value of the field's type found anywhere in the document (1-based)."""

    method: Literal["nth_match"]
    n: int = Field(ge=1)


Strategy = Annotated[LabelStrategy | RegexStrategy | NthMatchStrategy, Field(discriminator="method")]


class FieldSpec(_Strict):
    type: str
    description: str | None = None
    """Human description; also used as the LLM instruction for this field."""
    extract: list[Strategy] = []
    """Rule strategies tried in order; the first valid value wins."""
    checksum: str | None = None
    """Override the type's default checksum (`none` disables it)."""
    on_invalid_checksum: Literal["warn", "reject"] = "warn"

    @field_validator("type")
    @classmethod
    def _known_type(cls, v: str) -> str:
        if v not in VALUE_TYPES:
            raise ValueError(f"unknown type '{v}', available: {sorted(VALUE_TYPES)}")
        return v

    @field_validator("checksum")
    @classmethod
    def _known_checksum(cls, v: str | None) -> str | None:
        if v not in (None, "none") and v not in CHECKSUMS:
            raise ValueError(f"unknown checksum '{v}', available: {sorted(CHECKSUMS)}")
        return v

    def effective_checksum(self) -> str | None:
        if self.checksum == "none":
            return None
        return self.checksum or VALUE_TYPES[self.type].checksum


class Classification(_Strict):
    """Rule signals for recognizing a document type.

    Text is compared case- and diacritics-insensitively (OCR often loses Polish letters);
    keywords are substrings, so a stem like "odwołując" matches "Odwołującego".
    score = number of distinct `keywords` found in the first `pages` pages
          + `title_weight` if a line in the header is exactly one of `titles`.
    The type is a candidate when score >= `min_score` and no `exclude` phrase occurs in
    the header (first `header_lines` lines). The highest-scoring candidate wins; a tie
    means the document is not recognized (never guessed).
    """

    keywords: list[str] = []
    titles: list[str] = []
    title_weight: int = 3
    exclude: list[str] = []
    min_score: int = 2
    pages: int = 2
    header_lines: int = 25


class SectionSplit(_Strict):
    """Items are text sections: from a `start` label to an `end` label (or the next start).

    With `item_marker` a section is further split into several items at lines matching
    the marker (e.g. '^\\s*\\d+\\)' for "1) ...", "2) ..."); text before the first marker
    is then dropped. Without markers each section is one item.
    """

    method: Literal["section"]
    start: list[str] = Field(min_length=1)
    end: list[str] = []
    item_marker: str | None = None
    max_lines: int = 20


class MatchesSplit(_Strict):
    """Every regex match is one item. A named group whose name equals an item field
    (e.g. (?P<imie_nazwisko>...)) gives that field's value directly; other fields are
    extracted from the matched text with their own strategies."""

    method: Literal["matches"]
    pattern: str
    flags: list[Literal["IGNORECASE", "MULTILINE", "DOTALL"]] = []


Split = Annotated[SectionSplit | MatchesSplit, Field(discriminator="method")]


class ListSpec(_Strict):
    """A JSON array. `item` is the template of one element (fields, containers, lists)."""

    type: Literal["list"]
    description: str | None = None
    split: Split | None = None
    """How to find the items by rules; None = no rule (only an LLM can fill it later)."""
    scope: Literal["parent", "document"] = "parent"
    """Text a nested list searches: its parent item's text or the whole document."""
    item: Any
    max_items: int = 20
    unique_by: list[str] = []
    """Item fields identifying duplicates (e.g. the same person found twice)."""

    @field_validator("split", mode="before")
    @classmethod
    def _split_compiles(cls, v: Any) -> Any:
        for key in ("pattern", "item_marker"):
            if isinstance(v, dict) and v.get(key):
                _check_regex(v[key], key)
        return v


def _check_regex(pattern: str, what: str) -> None:
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"invalid regular expression in '{what}': {exc}") from exc


class DocumentType(_Strict):
    name: str
    description: str | None = None
    classification: Classification = Classification()
    stop_labels: list[str] = []
    output: dict[str, Any] = {}

    @model_validator(mode="after")
    def _parse_output(self) -> "DocumentType":
        self.output = _parse_template(self.output, path=self.name)
        return self

    def fields(self) -> dict[str, FieldSpec]:
        """Flat map of every leaf in the output template: 'a.b' (list items as 'a[].b')."""
        out: dict[str, FieldSpec] = {}

        def walk(node: Any, prefix: str) -> None:
            if isinstance(node, FieldSpec):
                out[prefix] = node
            elif isinstance(node, ListSpec):
                walk(node.item, f"{prefix}[]")
            else:
                for key, child in node.items():
                    walk(child, f"{prefix}.{key}" if prefix else key)

        walk(self.output, "")
        return out


def _parse_template(node: Any, path: str) -> Any:
    if not isinstance(node, dict):
        raise ValueError(f"{path}: expected a mapping (container) or a field spec with 'type'")
    if node.get("type") == "list":
        spec = ListSpec.model_validate(node)
        spec.item = _parse_template(spec.item, f"{path}[]")
        return spec
    if "type" in node:
        return FieldSpec.model_validate(node)
    return {key: _parse_template(child, f"{path}.{key}") for key, child in node.items()}


def load_document_types(directory: Path) -> dict[str, DocumentType]:
    """Load every *.yaml / *.yml file in `directory`."""
    types: dict[str, DocumentType] = {}
    for path in sorted([*directory.glob("*.yaml"), *directory.glob("*.yml")]):
        try:
            doc_type = DocumentType.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        except Exception as exc:
            raise ValueError(f"{path.name}: invalid document type definition: {exc}") from exc
        if doc_type.name in types:
            raise ValueError(f"{path.name}: duplicate document type name '{doc_type.name}'")
        types[doc_type.name] = doc_type
    return types
