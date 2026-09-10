"""Parsing of the Atlantic Cozytouch consumption endpoints.

The backend exposes consumption history through

    GET /magellan/setups/<setupId>/consumptions?periodicity=daily

which answers with one entry per measured series::

    [
      {
        "type": 1, "unit": 1, "currency": 101,
        "consumptionPeriods": [
          {"consumedQuantity": 3.87, "cost": 0.56, "date": 1789034400, "mode": 2},
          ...
        ]
      },
      ...
    ]

``type``/``unit`` identify what is measured, ``mode`` splits electricity between
peak and off-peak hours, and ``date`` is the start of the period.
"""

# Measured series, as observed on an ACI HYB water heater.
CONSUMPTION_TYPE_ELECTRICITY = 1
CONSUMPTION_TYPE_WATER = 4

CONSUMPTION_UNIT_KWH = 1
CONSUMPTION_UNIT_LITER = 2

# Tariff period electricity is billed under. Water is reported with mode 0.
CONSUMPTION_MODE_NONE = 0
CONSUMPTION_MODE_PEAK = 1
CONSUMPTION_MODE_OFFPEAK = 2

# The API reports the currency as a numeric code. Only 101 has been observed so
# far, on an installation billed in euros; anything else is left without a unit
# rather than guessed.
CONSUMPTION_CURRENCIES = {101: "EUR"}


def get_currency(currency: int | None) -> str | None:
    """Return the ISO currency code for an API currency id, if it is known."""
    return CONSUMPTION_CURRENCIES.get(currency)


def parse_latest_consumptions(json_data) -> dict:
    """Return the most recent period of every series in a consumptions payload.

    The result is keyed by ``(type, unit, mode)`` so that the electricity series
    stays split between its tariff periods, each entry holding the quantity, the
    cost, the currency and the start of the period.
    """
    result: dict = {}
    if not isinstance(json_data, list):
        return result

    for series in json_data:
        if not isinstance(series, dict):
            continue

        periods = series.get("consumptionPeriods")
        if not isinstance(periods, list):
            continue

        dates = [p["date"] for p in periods if isinstance(p, dict) and p.get("date")]
        if not dates:
            continue

        latest = max(dates)
        for period in periods:
            if not isinstance(period, dict) or period.get("date") != latest:
                continue

            key = (series.get("type"), series.get("unit"), period.get("mode"))
            result[key] = {
                "quantity": period.get("consumedQuantity"),
                "cost": period.get("cost"),
                "currency": series.get("currency"),
                "date": latest,
            }

    return result


def sum_field(consumptions: dict, consumptionType: int, field: str):
    """Total one field over every tariff period of a given series.

    Returns None when the series is absent, so that a sensor stays unavailable
    instead of reporting a misleading zero.
    """
    values = [
        entry[field]
        for key, entry in consumptions.items()
        if key[0] == consumptionType and entry.get(field) is not None
    ]
    if not values:
        return None

    return round(sum(values), 3)


def get_field(consumptions: dict, consumptionType: int, mode: int, field: str):
    """Read one field of a single tariff period of a series."""
    for key, entry in consumptions.items():
        if key[0] == consumptionType and key[2] == mode:
            return entry.get(field)

    return None


def get_series_currency(consumptions: dict, consumptionType: int) -> str | None:
    """Return the ISO currency the given series is billed in, when known."""
    for key, entry in consumptions.items():
        if key[0] == consumptionType and entry.get("currency") is not None:
            return get_currency(entry["currency"])

    return None
