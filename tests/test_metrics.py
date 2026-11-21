from src.evaluation.metrics import Counts, canonical, compare, flatten


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
    c = total(compare(ref, ref).strict)
    assert (c.tp, c.fp, c.fn, c.f1) == (2, 0, 0, 1.0)


def test_wrong_value_counts_as_fp_and_fn():
    c = total(compare({"a": "x"}, {"a": "y"}).strict)
    assert (c.tp, c.fp, c.fn) == (0, 1, 1)


def test_null_prediction_is_only_fn_and_extra_value_is_only_fp():
    assert total(compare({"a": None}, {"a": "y"}).strict).fn == 1
    extra = total(compare({"a": "x"}, {"a": None}).strict)
    assert (extra.fp, extra.fn) == (1, 0)


def test_empty_prediction_for_negative_document():
    assert total(compare({}, {}).strict) == Counts()
    assert total(compare({"a": "x"}, {}).strict).fp == 1


def test_lists_are_order_insensitive():
    pred = {"l": [{"n": "B"}, {"n": "A"}]}
    ref = {"l": [{"n": "A"}, {"n": "B"}, {"n": "C"}]}
    c = total(compare(pred, ref).strict)
    assert (c.tp, c.fp, c.fn) == (2, 0, 1)


def test_numbers_and_digit_strings():
    assert canonical(200, False) == canonical(200.0, False) == "200"
    assert canonical(85120133547, False) == canonical("85120133547", False)
    assert canonical("0000054588", False) == "0000054588"  # KRS keeps leading zeros


def test_lenient_mode_ignores_case_and_whitespace():
    result = compare({"a": "Kancelaria  Prawna."}, {"a": "kancelaria prawna"})
    assert total(result.strict).tp == 0
    assert total(result.lenient).tp == 1
    assert result.mismatches[0].path == "a"
