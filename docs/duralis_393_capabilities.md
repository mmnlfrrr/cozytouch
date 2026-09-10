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
| 230 | Writable `0`/`1` flag gating heating | Written `0` then `1`; both echoed. Setting `1` started heating (99 → `1`, 278 → `2100`). | High that it is writable; **medium** on the exact semantic (on/off vs. DHW enable) |
| 237–243 | Weekly schedule, **one capability per weekday** | In a single 200 ms burst the app wrote `[[0,58],[0,0],[0,0],[0,0]]` to 237, 238, 239, 240, 241 and `[[0,62],[0,0],[0,0],[0,0]]` to 242, 243 — a 5 + 2 split, i.e. Mon–Fri / Sat–Sun. All seven echoed back. | High for the per-day grouping; **the meaning of each `[a,b]` pair is not established** |

### About 237–243

Each value holds four `[a,b]` pairs. The 5 + 2 write grouping is solid evidence
that 237 = Monday … 243 = Sunday, but the pair contents are *not* identified:

- the second element moved `62 → 58` on weekdays and `65 → 62` at the weekend;
- the same numbers (`62`, `65`, `58`) also occur as temperatures elsewhere in the
  same session (caps 22, 231, 234, 312), so a time-slot reading and a
  setpoint reading are both plausible.

Not enough to choose. This needs a capture where a single schedule slot is moved
by a known amount, with the temperature left untouched.

---

## 2. Confirmed by correlation

No direct write, but the value moved in a reproducible, explainable way.

| ID | Meaning | Evidence | Confidence |
|---:|---|---|---|
| 105122 | Boost end time, **naive local-time epoch** | Set to a value exactly equal to the boost write time + 1440 min (the duration written to 232), to the second. Reset to `0` when the mode left boost. Decoded as UTC it yields the appliance's *local* wall-clock time (`12:49:43`, for a boost started at `12:49:41` local), so it must not be shifted by the timezone capability 315 as well. | High |
| 105906 / 105907 | Setpoint expressed as **% of the 15–65 °C range** | `65 °C → 100`, `62 °C → 94`, `50 °C → 70`, i.e. exactly `(T − 15) / 50 × 100`. Matches the `temperatureMin`/`temperatureMax` already declared for these ids. | High |
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

Capability **150** contains ten sub-arrays, not seven, so despite its shape it is
**not** a plain weekly schedule. The per-day schedule lives in 237–243 (above).

---

## 4. Platform notes

- **Capability 233 (`boost_remaining_time`) is absent on this device.** Only 232
  (total time) exists, so the boost countdown has to be derived from 105122
  (boost end timestamp) instead — this is what the `boost_end_time` sensor does.
- **Capability 269 (`water_consumption`) is `null`** on this device, even though
  the iOS app displays water usage. The app reads it from
  `GET /magellan/setups/<id>/consumptions` and
  `GET /magellan/gateways/<id>/consumptions`, which return `consumedQuantity`,
  `cost`, `currency`, `mode` and `date`. A `null` 269 therefore does **not** mean
  "no water data available".
- Capability 258 reports `150`, matching the 150 L tank of this model.
- Temperature bounds are reported consistently: 253/105301 = `50`,
  252/105300/105304/231/234 = `65`.
