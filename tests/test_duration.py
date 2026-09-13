"""Tests for the duration rendering used by the "time" capabilities.

Runs standalone (python3 tests/test_duration.py) or under pytest.
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "cozytouch")
)

from duration import format_duration  # noqa: E402


def test_below_an_hour_keeps_minutes():
    assert format_duration(0) == "0 min"
    assert format_duration(15) == "15 min"
    assert format_duration(59) == "59 min"


def test_whole_hours_drop_the_minutes():
    # The programming constraints of the Duralis 393: 480 minutes of minimum
    # heating per day and 1440 of maximum are the values the card has to make
    # readable at a glance.
    assert format_duration(60) == "1 h"
    assert format_duration(480) == "8 h"
    assert format_duration(1440) == "24 h"


def test_partial_hours_keep_two_digit_minutes():
    assert format_duration(90) == "1 h 30"
    assert format_duration(65) == "1 h 05"
    assert format_duration(1439) == "23 h 59"


def test_days_only_past_two_full_days():
    # 1440 stays "24 h" so a per-day constraint reads as a duration; a boost
    # counter that really has run for days switches to days.
    assert format_duration(2879) == "47 h 59"
    assert format_duration(2880) == "2 j"
    assert format_duration(3000) == "2 j 2 h"
    assert format_duration(100000) == "69 j 10 h"


def test_missing_or_invalid_stays_unknown():
    assert format_duration(None) is None
    assert format_duration("abc") is None


def test_strings_holding_a_number_are_accepted():
    # The API returns capability values as strings.
    assert format_duration("480") == "8 h"


def test_negative_keeps_its_sign():
    assert format_duration(-90) == "-1 h 30"


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
