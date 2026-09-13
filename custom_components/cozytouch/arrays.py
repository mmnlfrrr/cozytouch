"""Rendering of the capabilities whose value is a JSON array.

A handful of capabilities (the two error tables, and 101-104 on boilers) hold
a JSON array rather than a scalar. The integration used to answer the literal
string "array" for all of them, without even reading the value: the entity
then stated something that was not its value at all.

What the rows mean is not known. The error tables of a Duralis 393 read ten
rows of five integers whose first four fields never varied across every
capture taken, and nothing in the vendor application names the fields, so no
meaning is assigned here. The value is simply shown as it is, and exposed as
an attribute so it can be inspected without guessing.

Kept free of Home Assistant imports so it can be unit tested on its own.
"""

import json

# Home Assistant refuses a state longer than 255 characters. A table that long
# would be unreadable in a card anyway, so it is summarised instead.
MAX_STATE_LENGTH = 255


def parse_array(value):
    """Return the value as a list, or None when it is not an array."""
    if isinstance(value, list):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return None
        if isinstance(parsed, list):
            return parsed

    return None


def format_array(value) -> str | None:
    """Render an array capability as a state string."""
    if value is None:
        return None

    parsed = parse_array(value)
    if parsed is None:
        text = str(value)
        return text[:MAX_STATE_LENGTH] if text else None

    if not parsed:
        return "vide"

    compact = json.dumps(parsed, separators=(",", ":"))
    if len(compact) <= MAX_STATE_LENGTH:
        return compact

    return "%d enregistrements" % len(parsed)


def format_utc_offset(value) -> str | None:
    """Render a UTC offset given in seconds, as "GMT", "GMT+2", "GMT+5:30"."""
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return None

    if seconds == 0:
        return "GMT"

    sign = "+" if seconds > 0 else "-"
    hours, rest = divmod(abs(seconds), 3600)
    minutes = rest // 60
    # Half-hour and three-quarter-hour zones exist; truncating to the hour
    # would have turned GMT+5:30 into GMT+5.
    if minutes:
        return "GMT%s%d:%02d" % (sign, hours, minutes)

    return "GMT%s%d" % (sign, hours)
