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
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator

from src.validation.checksums import CHECKSUMS
from src.validation.normalizers import VALUE_TYPES, expand_placeholders


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


RegexFlag = Literal["IGNORECASE", "MULTILINE", "DOTALL"]


class _TextStrategy(_Strict):
    pages: int | None = None
    """Search only the first N pages (e.g. 1 for data from the letter header)."""


class LabelStrategy(_TextStrategy):
    """Value written after a label: on the same line or within the next `lookahead` lines."""

    method: Literal["label"]
    labels: list[str] = Field(min_length=1)
    lookahead: int = 2
    multiline: bool = False
    """Collect the value across lines until the next label / stop label (e.g. a transfer title)."""
    max_lines: int = 6
    until: str | None = None
    """Regex ending the value (for `text` fields), e.g. ',' for "adres: Kancelaria X, ul. ..."."""

    @field_validator("until")
    @classmethod
    def _until_compiles(cls, v: str | None) -> str | None:
        if v:
            _check_regex(v, "until")
        return v


class RegexStrategy(_TextStrategy):
    """Custom regular expression run over whole pages (`\\s` spans line breaks).

    `{value}` is replaced with the field type's pattern and `{<type>}` with any value
    type's pattern (e.g. `{date}`, `{person}`). `group` selects the capture group
    (default: first group, or the whole match when there is none).
    """

    method: Literal["regex"]
    pattern: str
    group: int | str | None = None
    flags: list[RegexFlag] = ["IGNORECASE"]

    @field_validator("pattern")
    @classmethod
    def _compiles(cls, v: str) -> str:
        _check_regex(expand_placeholders(v, "text"), "pattern")
        return v


class NthMatchStrategy(_TextStrategy):
    """The n-th distinct value of the field's type found in the text (1-based)."""

    method: Literal["nth_match"]
    n: int = Field(ge=1)


class KeywordRule(_Strict):
    value: Any
    any: list[str] = Field(min_length=1)


class KeywordMapStrategy(_TextStrategy):
    """Choose a value by keywords: the first rule with any keyword present wins.

    Matching is case- and diacritics-insensitive. `within` (regex with one group) narrows
    the text to a fragment, e.g. the sentence describing the appealed action.
    """

    method: Literal["keyword_map"]
    within: str | None = None
    map: list[KeywordRule] = Field(min_length=1)
    default: Any = None

    @field_validator("within")
    @classmethod
    def _within_compiles(cls, v: str | None) -> str | None:
        if v:
            _check_regex(expand_placeholders(v, "text"), "within")
        return v


class DerivedStrategy(_Strict):
    """Value computed from another field of the same object (path relative to it)."""

    method: Literal["derived"]
    source: str = Field(alias="from")
    if_present: Any = None
    if_absent: Any = None


class LookupStrategy(_Strict):
    """Translate another field's value with a dictionary from config/dictionaries/<name>.yaml."""

    method: Literal["lookup"]
    source: str = Field(alias="from")
    dictionary: str


Strategy = Annotated[
    LabelStrategy | RegexStrategy | NthMatchStrategy | KeywordMapStrategy | DerivedStrategy | LookupStrategy,
    Field(discriminator="method"),
]
DEPENDENT_STRATEGIES = (DerivedStrategy, LookupStrategy)


class FieldSpec(_Strict):
    type: str
    description: str | None = None
    """Human description; also used as the LLM instruction for this field."""
    extract: list[Strategy] = []
    """Rule strategies tried in order; the first valid value wins."""
    checksum: str | None = None
    """Override the type's default checksum (`none` disables it)."""
    on_invalid_checksum: Literal["warn", "reject"] = "warn"
    must_match: str | None = None
    """Regex the (normalized) value must contain, e.g. '^[A-ZĄĆĘŁŃÓŚŹŻ]' for a name.
    A candidate that does not match is skipped — a wrong value costs more than null."""
    reject: list[str] = []
    """Regexes of values to skip, e.g. bare labels such as '^(KRS|NIP|tel)\\b'."""
    llm: Literal["fill", "prefer", "arbitrate", "never"] = "fill"
    """Hybrid mode: fill = the model only fills a value the rules did not find;
    prefer = a valid model value wins over the rule; arbitrate = when the rule and the model
    disagree, a short second model call chooses between them using both source fragments;
    never = the model is ignored. Derived / lookup fields are always recomputed."""
    llm_evidence: bool = False
    """Ask the model to quote the document fragment it based the value on (key '<field>_cytat'),
    before giving the value — improves reasoning of small models and is shown as the source."""

    @field_validator("must_match")
    @classmethod
    def _must_match_compiles(cls, v: str | None) -> str | None:
        if v:
            _check_regex(v, "must_match")
        return v

    @field_validator("reject")
    @classmethod
    def _reject_compiles(cls, v: list[str]) -> list[str]:
        for pattern in v:
            _check_regex(pattern, "reject")
        return v

    def plausible(self, value: Any) -> str | None:
        """None if the value passes must_match/reject, else the reason it was skipped."""
        if not isinstance(value, str):
            return None
        if self.must_match and not re.search(self.must_match, value):
            return f"skipped '{value}': does not match must_match"
        for pattern in self.reject:
            if re.search(pattern, value, re.IGNORECASE):
                return f"skipped '{value}': matches reject"
        return None

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

    @property
    def is_dependent(self) -> bool:
        """Uses values of other fields, so it is filled after them."""
        return any(isinstance(s, DEPENDENT_STRATEGIES) for s in self.extract)


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
    heading_only: bool = True
    """A start label must look like a heading — followed by ':' or '(' or the end of the
    line — so a sentence such as "Zamawiający w dniu ..." does not open a section."""


class MatchesSplit(_Strict):
    """Every regex match is one item. A named group whose name equals an item field
    (e.g. (?P<imie_nazwisko>...)) gives that field's value directly; other fields are
    extracted from the matched text with their own strategies."""

    method: Literal["matches"]
    pattern: str
    """`{<type>}` placeholders are expanded as in the regex strategy."""
    flags: list[RegexFlag] = []
    min_items: int = 1
    """Fewer matches than this = this split does not apply (the next alternative is tried)."""


class WholeSplit(_Strict):
    """The whole text (optionally only the first `pages` pages) is a single item."""

    method: Literal["whole"]
    pages: int | None = None


Split = Annotated[SectionSplit | MatchesSplit | WholeSplit, Field(discriminator="method")]


class ListSpec(_Strict):
    """A JSON array. `item` is the template of one element (fields, containers, lists)."""

    type: Literal["list"]
    description: str | None = None
    split: Split | list[Split] | None = None
    """How to find the items by rules; a list = alternatives, the first one producing
    items wins. None = no rule (only an LLM can fill it later)."""
    scope: Literal["parent", "document"] = "parent"
    """Text a nested list searches: its parent item's text or the whole document.
    With `document` and `unique_by`, an item found for one parent is not repeated under
    the next parents (it cannot be attributed, so it is listed once)."""
    item: Any
    max_items: int = 20
    unique_by: list[str] = []
    """Item fields identifying duplicates (e.g. the same person found twice)."""

    @field_validator("split", mode="before")
    @classmethod
    def _split_compiles(cls, v: Any) -> Any:
        for alternative in v if isinstance(v, list) else [v]:
            for key in ("pattern", "item_marker"):
                if isinstance(alternative, dict) and alternative.get(key):
                    _check_regex(expand_placeholders(alternative[key], None), key)
        return v

    def splits(self) -> list[Any]:
        if self.split is None:
            return []
        return self.split if isinstance(self.split, list) else [self.split]


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
    _dictionaries: dict[str, dict[Any, Any]] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def _parse_output(self) -> "DocumentType":
        self.output = _parse_template(self.output, path=self.name)
        return self

    def dictionary_names(self) -> set[str]:
        names: set[str] = set()

        def walk(node: Any) -> None:
            if isinstance(node, FieldSpec):
                names.update(s.dictionary for s in node.extract if isinstance(s, LookupStrategy))
            elif isinstance(node, ListSpec):
                walk(node.item)
            else:
                for child in node.values():
                    walk(child)

        walk(self.output)
        return names

    def load_dictionaries(self, directory: Path) -> None:
        """Load config/dictionaries/<name>.yaml for every lookup strategy (fails on a missing file)."""
        for name in self.dictionary_names():
            path = directory / f"{name}.yaml"
            if not path.exists():
                raise ValueError(f"dictionary '{name}' not found: {path}")
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError(f"dictionary '{name}' must be a mapping key -> value")
            self._dictionaries[name] = data

    def dictionary(self, name: str) -> dict[Any, Any]:
        return self._dictionaries.get(name, {})

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


def load_document_types(directory: Path, dictionaries_dir: Path | None = None) -> dict[str, DocumentType]:
    """Load every *.yaml / *.yml file in `directory` (dictionaries default to ../dictionaries)."""
    dictionaries_dir = dictionaries_dir or directory.parent / "dictionaries"
    types: dict[str, DocumentType] = {}
    for path in sorted([*directory.glob("*.yaml"), *directory.glob("*.yml")]):
        try:
            doc_type = DocumentType.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
            doc_type.load_dictionaries(dictionaries_dir)
        except Exception as exc:
            raise ValueError(f"{path.name}: invalid document type definition: {exc}") from exc
        if doc_type.name in types:
            raise ValueError(f"{path.name}: duplicate document type name '{doc_type.name}'")
        types[doc_type.name] = doc_type
    return types
