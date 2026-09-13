"""Tests for the array and UTC offset rendering."""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "cozytouch")
)

from arrays import format_array, format_utc_offset, parse_array  # noqa: E402

# The error table an ACI HYB 393 reports, verbatim from a capture.
ERROR_TABLE = (
    "[[0,255,0,4,0],[0,255,0,4,0],[0,255,0,4,0],[0,255,0,4,0],[0,255,0,4,0],"
    "[0,255,0,4,102],[0,255,0,4,0],[0,255,0,4,0],[0,255,0,4,255],[0,255,0,4,0]]"
)


def test_the_error_table_is_shown_instead_of_the_word_array():
    rendered = format_array(ERROR_TABLE)
    assert rendered != "array"
    assert rendered.startswith("[[0,255,0,4,0]")
    assert len(rendered) <= 255


def test_rows_are_parsed_for_the_attribute():
    rows = parse_array(ERROR_TABLE)
    assert len(rows) == 10
    assert rows[5] == [0, 255, 0, 4, 102]


def test_an_empty_array_says_so():
    assert format_array("[]") == "vide"
    assert format_array([]) == "vide"


def test_a_table_too_long_for_a_state_is_summarised():
    long_table = "[" + ",".join(["[0,255,0,4,0]"] * 40) + "]"
    assert len(long_table) > 255
    assert format_array(long_table) == "40 enregistrements"


def test_a_value_that_is_not_an_array_is_left_alone():
    assert parse_array("nope") is None
    assert format_array("nope") == "nope"
    assert format_array(None) is None


def test_whole_hour_offsets():
    assert format_utc_offset(7200) == "GMT+2"
    assert format_utc_offset("7200") == "GMT+2"
    assert format_utc_offset(0) == "GMT"
    assert format_utc_offset(-18000) == "GMT-5"


def test_half_hour_offsets_keep_their_minutes():
    # Used to be truncated to "GMT+5".
    assert format_utc_offset(19800) == "GMT+5:30"
    assert format_utc_offset(-12600) == "GMT-3:30"
    assert format_utc_offset(20700) == "GMT+5:45"


def test_a_missing_offset_stays_unknown():
    assert format_utc_offset(None) is None
    assert format_utc_offset("abc") is None


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok   %s" % name)
            except AssertionError as err:
                failures += 1
                print("FAIL %s: %s" % (name, err))
    print("%d failure(s)" % failures)
    sys.exit(1 if failures else 0)
