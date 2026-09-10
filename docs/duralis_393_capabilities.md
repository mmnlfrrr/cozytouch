# Duralis Connect ACI HYB VM 150L 2200M (modelId 393) — capability notes

Reference notes for the ACI HYB hybrid water-heater platform, gathered from a
real **Thermor Duralis Connect ACI HYB VM 150 L 2200 W** (`modelId 393`).

Evidence comes from a proxied capture of the official Cozytouch iOS app:
52 successive `GET /magellan/capabilities/` snapshots interleaved with
23 `POST /magellan/executions/writecapability` calls, which makes it possible to
correlate each write with the capability values that changed afterwards.

The raw capture is **not** part of this repository: it contains bearer tokens,
account identifiers and installation ids. All device / setup / gateway ids below
are redacted.

Ground rule for this document: **a capability is only considered identified once a
change has been reproduced and correlated.** Anything else is listed as unknown,
even when its value looks suggestive.

The device exposes **87 capabilities**.

---

## 1. Confirmed by write + read-back

These were written by the iOS app and the new value was observed in a later
`capabilities` snapshot.

| ID | Meaning | Evidence | Confidence |
|---:|---|---|---|
| 87 | Heating mode | Written with `0`, `4`, `3`, `4`, `3` in five separate actions; each value echoed back in capability 87. Matches the existing ACI HYB `HeatingModes` map (`0` = manual, `3` = eco+, `4` = prog). | High |
| 165 | Boost on/off | Written `1` → 165 became `1`; written `0` → 165 became `0`. | High |
| 232 | Boost duration, **minutes** | Written `1440` → 232 became `1440`; written `0` → 232 became `0`. Also reset to `0` by the device when the mode left boost. | High |
| 230 | Selects **permanent heating (`0`)** vs **heating restricted to the daily time ranges (`1`)** | Toggled from the app outside the configured ranges: `-> 0` started the resistance within the minute (278 -> `2100`, pump on) and `-> 1` stopped it (278 -> `0`, pump off). Matches a screenshot showing "custom ranges" selected while 230 sat at `1`. | High |
| 237–243 | Programmed DHW temperature, **one capability per day**, Monday (237) to Sunday (243) | In a single 200 ms burst the app wrote the same value to 237–241 and another to 242–243 — a 5 + 2 split. A later capture of the "hot water quantity" screen showed Mon–Fri on one value and Sat/Sun on a higher one, matching the capability values position by position. | High |

### About 237–243 and 245–251

The weekly program is split across two blocks of seven capabilities, both
ordered Monday first, which is the order the integration already assumes for
245–251 (`prog_01 (Mon)` … `prog_07 (Sun)`):

- **245–251 carry the times**, as pairs of minutes since midnight. The observed
  `[[0,435],[1395,1440],[0,0]]` decodes to `00:00–07:15 / 23:15–24:00`, and the
  app renders exactly those bars. A capture in which a single day's range was
  moved wrote `435 → 450` to capability 245 alone and then back — 07:15 to 07:30
  and back — which fixes both the unit and the per-day mapping.
- **237–243 carry the setpoints**, in degrees, and per the owner of the
  appliance they apply **only in prog mode**, whereas the time ranges in
  245–251 apply in every mode. Entering prog mode makes the
  effective setpoint (312) take exactly the value held by the *current* day:
  observed twice on a Thursday, once at `62` and once at `58`, each time with
  the weekday capabilities holding that value. Capability 105906 tracked it as
  `86`, i.e. `(58 − 15) / 50 × 100`, confirming the degrees reading.

Note that the app does **not** display these degrees directly: its "hot water
quantity" screen showed `80 %` for a stored `58` and `90 %` for a stored `62`,
which is a different scale from the one capability 105906 uses. Two points fit
`pct = 2.5 × T − 65`, but that is a fit through two values, not an established
mapping — the integration exposes the degrees actually on the wire and leaves
the app's presentation scale alone.

The **first element of each pair in 237–243 is the minute the slot starts**, so
`[[0,58],[0,0],[0,0],[0,0]]` reads "58 °C from 00:00", with three unused slots.
That is the format upstream PR #165 documents for the weekly programs of
thermostats, where a day is stored as `[[minutes, temperature], ...]`; it fits
every value seen here, and explains why the first element has always been `0` —
the app only ever offers a single setpoint per day, starting at midnight.

Note this differs from the neighbouring time block: 245–251 hold
`[start, end]` ranges, not `[start, value]` pairs. Both readings are pinned by
the same capture — `[0,435]` and `[1395,1440]` line up with the app drawing
bars at 00:00–07:15 and 23:15–24:00, and moving one range wrote `435 → 450`,
i.e. the *end* of the first window.

### Writing the program

Both blocks are written by replacing the whole array, exactly as the app does:

```
{"deviceId": <id>, "capabilityId": 237, "value": "[[0,58],[0,0],[0,0],[0,0]]"}
{"deviceId": <id>, "capabilityId": 245, "value": "[[0,450],[1395,1440],[0,0]]"}
```

Because every day has its own capability, writing one day cannot disturb the
others.

The setpoints are exposed as writable numbers, one per day. They rewrite the
temperature of the first slot, leaving its start minute and the remaining slots
untouched, so the shape sent back is byte for byte the one the app sends. A day
holding several setpoint slots would therefore only expose its first through
this entity, which matches what the app offers. Bounds come from 253/252 (50–65 °C).
Note that the app itself only offers its percentage scale in steps of about
4 °C; whether the appliance accepts arbitrary values in between has not been
tested.

The **time ranges are left read-only** for now. Their format is understood —
pairs of minutes since midnight, up to three slots per day — but exposing them
would mean either twenty-eight time entities or a service, and this integration
declares no services at all today. Documented here so it can be added
deliberately rather than as a side effect.

---

## 2. Confirmed by correlation

No direct write, but the value moved in a reproducible, explainable way.

| ID | Meaning | Evidence | Confidence |
|---:|---|---|---|
| 105122 | Boost end time, **naive local-time epoch** | Set to a value exactly equal to the boost write time + 1440 min (the duration written to 232), to the second. Reset to `0` when the mode left boost. Decoded as UTC it yields the appliance's *local* wall-clock time (`12:49:43`, for a boost started at `12:49:41` local), so it must not be shifted by the timezone capability 315 as well. | High |
| 312 | The setpoint **currently applied** | It follows the active mode rather than a stored preference: 65 under boost while 22 stayed at 50, back to 50 in eco+, and the value held by the current day of the program in prog mode. Five mode changes, each matching. | High |
| 105906 / 105907 | Setpoint expressed as **% of the 15–65 °C range**, 105906 mirroring 312 and 105907 mirroring 22 | `65 °C → 100`, `62 °C → 94`, `58 °C → 86`, `50 °C → 70`, i.e. exactly `(T − 15) / 50 × 100`. Each moved in the same snapshot as the capability it mirrors, six times. | High |
| 99 | Resistance / heating active | `0 → 1` when heating began, `→ 0` once the device settled in prog. | High |
| 278 | Electrical power drawn (W) | Toggled `0 ↔ 2100` in lockstep with 99, on a 2200 W appliance. | Medium |
| 281 | Secondary heating flag | Toggled `0 ↔ 1` in lockstep with 99. | Medium |
| 339 | Inverse of 99 (idle flag) | `1 → 0` as heating started, back to `1` when it stopped. | Medium |
| 337 / 338 | Activity / mode state | 337 took `2` under boost, `6` under prog, `0` at rest; 338 was consistently its boolean inverse. | Low |
| 292 | Hot-water level requested | Followed the selected mode: boost and manual → `5`, prog → `4`, eco+ → `1`. Small integers — **not** a percentage. | Medium, consistent with PR #155 |
| 293 | Current hot-water level | `1 → 0` when heating began. Same small-integer domain as 292. | Medium, consistent with PR #155 |

---

## 3. Still unknown

Present on the device, no reproducible correlation observed. Listed with an
example value only, deliberately **without** any proposed meaning:

| ID | Example |
|---:|---|
| 15 | `2` |
| 150 | ten sub-arrays of `[0,255,0,4,x]` |
| 164 | `1040` |
| 168 | `16141` |
| 188 | `2` |
| 223 | `3` |
| 224 | `125` |
| 234 | `65.0` |
| 236 | `1` |
| 244 | `3` |
| 284–290, 307–311, 329–336, 340, 351, 381 | assorted |
| 105011 / 105012 | assorted |

One lead worth recording, and worth resisting: capability 168 reads `16141`
while the consumptions endpoint reports `16148.84` litres of water for the year,
which is tempting. It is not enough. Over a half hour in which water was clearly
being drawn — the available V40 volume in 268 fell from 118 to 107 — capability
168 did not move at all, which is the opposite of what a live water counter
would do. Left unidentified.

None of the other capabilities above changed during any of the captures, so
identifying them needs either a much longer history or an action in the app
known to touch them.

Capability **150** contains ten sub-arrays, not seven, so despite its shape it is
**not** a plain weekly schedule. The weekly program lives in 245–251 (times)
and 237–243 (setpoints), both described above.

## 3b. How capability 230 was pinned down

230 was first taken for a plain on/off flag, because writing `1` appeared to
start heating. That was a polling artefact: the appliance reacts to the setting
with a delay of a few seconds, so the heating that showed up alongside a `1`
was in fact the effect of the `0` written ten seconds earlier.

Toggling the setting deliberately, outside the configured ranges, separated the
two cleanly:

```
13:27:08   230 -> 0    278 -> 2100   281 -> 1   339 -> 0   pump on
13:30:08   230 -> 1    278 -> 0      281 -> 0   339 -> 1   pump off
```

With ranges of `00:00–07:15` and `23:15–24:00`, both timestamps fall outside
them, so `0` lifting the restriction and `1` reinstating it is the only reading
that fits — and it agrees with a screenshot taken earlier showing "custom
ranges" selected while 230 read `1`.

This also accounts for heating seen running in eco+ outside the ranges: at that
point the setting had just been moved to permanent.

## 3c. Field data that contradicts an open upstream change

Upstream PR #146 proposes renumbering the tank sensors to
`264 = bottom, 265 = middle, 266 = top, 267 = average`. On this appliance that
last one does not hold:

| Capability | Reading |
|---:|---:|
| 264 | 27.24 °C |
| 265 | 44.47 °C |
| 266 | 49.97 °C |
| 267 | 24.43 °C |

267 is **colder than all three others**, so it cannot be their average, which
would fall around 40.6 °C. The current upstream naming — 267 as the bottom of
the tank, the coldest point of a stratified cylinder, with 264 the condenser of
the heat pump — is consistent with these readings, and 264/265/266 do not fit a
bottom/middle/top ordering on their own since 264 sits between the bottom and
the middle.

This is one appliance, and PR #146 cites Atlantic's own capability list, so it
may simply be that the numbering differs across families. Worth checking against
a second ACI HYB before either naming is treated as settled.

## 3d. Two presentation details worth keeping

- Capabilities that hold "nothing scheduled" report `0`, not an absent value.
  Sensors built on them return `None` so Home Assistant shows its own localised
  "unknown"; returning a literal `"Undefined"` leaks an English word into every
  other language.
- The two away-mode `datetime` entities have to stay writable while absence is
  off. Turning the absence switch on reads whatever range they hold and falls
  back to "in one minute, for two days" when none is set, so making them
  unavailable would remove the only way to choose the dates beforehand.

## 4. Platform notes

- **Capability 233 (`boost_remaining_time`) is absent on this device.** Only 232
  (total time) exists, so the boost countdown has to be derived from 105122
  (boost end timestamp) instead — this is what the `boost_end_time` sensor does.
- **Consumption history comes from its own endpoint**, not from capabilities:
  `GET /magellan/setups/<id>/consumptions?periodicity=daily|monthly|yearly`.
  Each series carries a `type`/`unit` pair and a list of periods:

  | type | unit | Meaning | mode |
  |---:|---:|---|---|
  | 1 | 1 | Electricity, kWh | `1` = peak hours, `2` = off-peak hours |
  | 4 | 2 | Water, litres | `0`, and always with a cost of `0` |

  The tariff modes were read off the costs and then confirmed against the app's
  own tariff screen: mode 1 divides out to `36.16 / 167.47 = 0.2159` per kWh and
  the app shows peak hours at `0.2159 €`, mode 2 gives `74.06 / 515.36 = 0.1437`
  against `0.1438 €` for off-peak. That screen also settles `currency: 101`,
  the only code seen, as euros.

- **Capability 269 (`water_consumption`) is `null`** on this device, even though
  the iOS app displays water usage. The app reads it from
  `GET /magellan/setups/<id>/consumptions` and
  `GET /magellan/gateways/<id>/consumptions`, which return `consumedQuantity`,
  `cost`, `currency`, `mode` and `date`. A `null` 269 therefore does **not** mean
  "no water data available": the water series above reported 109 litres for the
  same day the capability read `null`. Since it can only ever read unknown on
  these models, the entity is not created while the capability is null.
- Capability 258 reports `150`, matching the 150 L tank of this model.
- Capability 271 reports `35` and the app shows "35 % of hot water available",
  confirming the existing `hot_water_available` percentage mapping.
- Temperature bounds are reported consistently: 253/105301 = `50`,
  252/105300/105304/231/234 = `65`.
