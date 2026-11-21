from src.evaluation.metrics import Counts, canonical, compare, flatten, similarity


def total(per_path: dict[str, Counts]) -> Counts:
    out = Counts()
    for c in per_path.values():
        out += c
    return out


def test_flatten_lists_and_nesting():
    obj = {"a": {"b": 1}, "l": [{"x": 1}, {"x": 2}]}
    assert list(flatten(obj)) == [("a.b", 1), ("l[].x", 1), ("l[].x", 2)]


def test_exact_match_is_all_true_positives():
    ref = {"p": {"kwota": 200.0, "tytul": "abc", "nr": None}}
    c = total(compare(ref, ref).exact)
    assert (c.tp, c.fp, c.fn, c.f1) == (2, 0, 0, 1.0)


def test_wrong_value_counts_as_fp_and_fn():
    c = total(compare({"a": "x"}, {"a": "y"}).exact)
    assert (c.tp, c.fp, c.fn) == (0, 1, 1)


def test_null_prediction_is_only_fn_and_extra_value_is_only_fp():
    assert total(compare({"a": None}, {"a": "y"}).exact).fn == 1
    extra = total(compare({"a": "x"}, {"a": None}).exact)
    assert (extra.fp, extra.fn) == (1, 0)


def test_empty_prediction_for_negative_document():
    assert total(compare({}, {}).exact) == Counts()
    assert total(compare({"a": "x"}, {}).exact).fp == 1


def test_lists_are_matched_by_content_not_order():
    pred = {"l": [{"n": "B"}, {"n": "A"}]}
    ref = {"l": [{"n": "A"}, {"n": "B"}, {"n": "C"}]}
    c = total(compare(pred, ref).exact)
    assert (c.tp, c.fp, c.fn) == (2, 0, 1)


def test_numbers_and_digit_strings():
    assert canonical(200) == canonical(200.0) == "200"
    assert canonical(85120133547) == canonical("85120133547")
    assert canonical("0000054588") == "0000054588"  # KRS keeps leading zeros


def test_uzp_mode_accepts_similar_long_strings_only_for_configured_fields():
    pred = {"nazwa": "Kancelaria Adwokacka Spółka z o.o.", "nip": "5540240548"}
    ref = {"nazwa": "Kancelaria Adwokacka Spółka z o. o.", "nip": "5540240549"}
    result = compare(pred, ref, {"nazwa": 0.8})
    assert result.uzp["nazwa"] == Counts(tp=1)
    assert result.exact["nazwa"] == Counts(fp=1, fn=1)
    assert result.uzp["nip"] == Counts(fp=1, fn=1)  # not a long-string field: must be exact
    assert [m.path for m in result.mismatches] == ["nazwa", "nip"]


def test_uzp_mode_rejects_dissimilar_strings_and_pairs_list_items_once():
    assert compare({"t": "Dostawa sprzętu"}, {"t": "Budowa drogi gminnej"}, {"t": 0.8}).uzp["t"].tp == 0
    pred = {"l": [{"n": "Alfa Serwis S.A."}, {"n": "Alfa Serwis SA"}]}
    ref = {"l": [{"n": "Alfa Serwis S.A."}]}
    assert compare(pred, ref, {"l[].n": 0.8}).uzp["l[].n"] == Counts(tp=1, fp=1)


def test_similarity_bounds():
    assert similarity("abc", "abc") == 1.0
    assert similarity("abc", "xyz") == 0.0


def test_digits_only_paths_ignore_account_prefix_in_uzp_mode():
    pred = {"r": "PL61109010140000071219812874"}
    ref = {"r": "61109010140000071219812874"}
    result = compare(pred, ref, digits_only={"r"})
    assert result.uzp["r"].tp == 1
    assert result.exact["r"].tp == 0
