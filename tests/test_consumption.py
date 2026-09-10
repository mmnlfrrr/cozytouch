"""Tests for the consumption payload parsing.

Runs against a sanitised fixture, never against the cloud API. Executable
either with pytest or directly with ``python tests/test_consumption.py``.
"""

import importlib.util
import json
import pathlib

# consumption.py is plain Python with no Home Assistant imports, so it is loaded
# straight from its path: that keeps this test runnable without installing the
# integration's runtime dependencies.
_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "cozytouch"
    / "consumption.py"
)
_spec = importlib.util.spec_from_file_location("cozytouch_consumption", _MODULE_PATH)
consumption = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(consumption)

CONSUMPTION_MODE_OFFPEAK = consumption.CONSUMPTION_MODE_OFFPEAK
CONSUMPTION_MODE_PEAK = consumption.CONSUMPTION_MODE_PEAK
CONSUMPTION_TYPE_ELECTRICITY = consumption.CONSUMPTION_TYPE_ELECTRICITY
CONSUMPTION_TYPE_WATER = consumption.CONSUMPTION_TYPE_WATER
get_currency = consumption.get_currency
get_field = consumption.get_field
get_series_currency = consumption.get_series_currency
parse_latest_consumptions = consumption.parse_latest_consumptions
sum_field = consumption.sum_field

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "consumptions_daily.json"


def load():
    """Load the sanitised daily consumptions fixture."""
    with FIXTURE.open(encoding="utf-8") as fixture:
        return parse_latest_consumptions(json.load(fixture))


def test_keeps_only_the_latest_period():
    """Only the most recent day of each series is retained."""
    parsed = load()
    dates = {entry["date"] for entry in parsed.values()}
    assert len(dates) == 1


def test_electricity_is_split_per_tariff_period():
    """Peak and off-peak stay separate, and add up to the daily total."""
    parsed = load()
    offpeak = get_field(
        parsed, CONSUMPTION_TYPE_ELECTRICITY, CONSUMPTION_MODE_OFFPEAK, "quantity"
    )
    peak = get_field(
        parsed, CONSUMPTION_TYPE_ELECTRICITY, CONSUMPTION_MODE_PEAK, "quantity"
    )
    assert offpeak == 3.87
    assert peak == 1.16
    assert sum_field(parsed, CONSUMPTION_TYPE_ELECTRICITY, "quantity") == 5.03


def test_cost_is_totalled_over_tariff_periods():
    """The daily cost adds up both tariff periods."""
    parsed = load()
    assert sum_field(parsed, CONSUMPTION_TYPE_ELECTRICITY, "cost") == 0.81


def test_water_is_reported_in_its_own_series():
    """Water comes as its own series, with no cost attached."""
    parsed = load()
    assert sum_field(parsed, CONSUMPTION_TYPE_WATER, "quantity") == 109


def test_zero_is_kept_and_missing_series_is_none():
    """A real zero survives, while an absent series reads as None."""
    parsed = load()
    # Water is reported with a cost of exactly 0, which must not be dropped.
    assert sum_field(parsed, CONSUMPTION_TYPE_WATER, "cost") == 0
    # Nothing on this device reports series type 99.
    assert sum_field(parsed, 99, "quantity") is None
    assert get_field(parsed, 99, CONSUMPTION_MODE_PEAK, "quantity") is None


def test_currency_comes_from_the_payload():
    """The currency is read from the payload, and unknown codes stay unset."""
    parsed = load()
    assert get_series_currency(parsed, CONSUMPTION_TYPE_ELECTRICITY) == "EUR"
    assert get_currency(101) == "EUR"
    assert get_currency(999) is None
    assert get_currency(None) is None


def test_malformed_payloads_do_not_raise():
    """Anything unexpected parses to an empty result instead of raising."""
    for payload in (
        None,
        {},
        [],
        [None],
        ["nonsense"],
        [{"consumptionPeriods": None}],
        [{"consumptionPeriods": []}],
        [{"type": 1, "consumptionPeriods": [{"date": None}]}],
        [{"type": 1, "consumptionPeriods": [None]}],
    ):
        assert parse_latest_consumptions(payload) == {}


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_") and callable(test):
            test()
            print("ok", name)
    print("all tests passed")
