"""Human readable rendering of the durations the device reports in minutes.

Every capability the integration types as "time" is a duration, never a time
of day: remaining override time, boost time, and the programming constraints
(minimum and maximum heating time per day, programming step, minimum and
maximum length of a range). Rendering them as "08:00" therefore read like a
clock, which is exactly the wrong reading. This module spells the unit out
instead, so "8 h" cannot be mistaken for eight o'clock.

Kept free of Home Assistant imports so it can be unit tested on its own.
"""

MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 60 * 24

# Below two days, hours stay easier to compare than days: a "maximum heating
# time per day" of 1440 minutes means twenty-four hours, not "one day zero".
DAY_THRESHOLD_MINUTES = 2 * MINUTES_PER_DAY


def format_duration(value) -> str | None:
    """Render a duration given in minutes, unit included.

    Returns None when the value is missing or not a number, so callers can
    leave the entity unknown rather than display a placeholder.
    """
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return None

    if minutes < 0:
        return "-" + format_duration(-minutes)

    if minutes >= DAY_THRESHOLD_MINUTES:
        days, rest = divmod(minutes, MINUTES_PER_DAY)
        hours = rest // MINUTES_PER_HOUR
        return "%d j %d h" % (days, hours) if hours else "%d j" % days

    if minutes >= MINUTES_PER_HOUR:
        hours, rest = divmod(minutes, MINUTES_PER_HOUR)
        return "%d h %02d" % (hours, rest) if rest else "%d h" % hours

    return "%d min" % minutes
