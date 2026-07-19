# Technical Implementation Plan — TS-001

**Rule:** TS-001 — Primary Target Zone (PTZ) Selection
**Source specification:** TS-001 (frozen)
**Governing specifications:** DR-001, TM-001, DS-001, CFG-001
**Scope:** Selection logic only. This plan introduces no trading rule, threshold, or behaviour beyond the approved specifications.

---

## 1. Objective

Implement TS-001 as a pure, stateless selection rule that, for a single invocation, returns the one Daily Fair Value Gap (FVG) that becomes the Primary Target Zone (PTZ), or reports that none qualifies.

The implementation shall:

- Detect candidate Daily FVGs via DR-001.
- Restrict candidates to the LOOKBACK_DAYS window anchored on the latest completed Daily candle.
- Remove candidates listed in the caller-supplied Excluded FVG Set.
- Remove candidates classified TESTED by TM-001.
- Rank the survivors by distance from Current Market Price to their nearest boundary, breaking ties by newest Candle C.
- Return exactly one PTZ, or `No PTZ Found`.

The implementation shall retain no state between invocations and shall return an identical result for identical inputs. Invocation timing, PTZ lifetime, PTZ completion, and construction of the Excluded FVG Set are outside this scope and belong to the orchestration layer.

The lifecycle boundary is normative, not advisory: any behaviour that would require TS-001 to remember a prior invocation, decide when it runs, or interpret why an FVG was excluded is out of scope by specification and must not be implemented here.

---

## 2. Dependencies

| Spec | Role in TS-001 | Consumed as |
|---|---|---|
| **DR-001** | Daily FVG detection. Produces the RawFVG candidate pool. | Called in Step 1. |
| **TM-001** | Touch detection. Classifies each candidate TESTED / UNTESTED. | Called in Step 4. |
| **DS-001** | Market data contract. Defines completed-candle guarantee, timestamp identity, calendar-day interpretation, price precision. | Governs all candle and timestamp handling. |
| **CFG-001** | Configuration. Supplies LOOKBACK_DAYS (default 14) and the fixed methods PTZ_SELECTION_METHOD = NEAREST and FVG_INVALIDATION = FIRST_TOUCH. | Read at Step 2 (window) and honoured throughout. |

Notes on the dependency contract:

- **DS-001 guarantees only completed Daily candles are supplied.** No completion check is implemented in TS-001; the guarantee is a precondition on input data, not a runtime test.
- **DS-001 requires unique, strictly chronological timestamps.** TS-001 relies on this for both the exclusion identifier and the tie-break. Enforcement of the guarantee is DS-001's; TS-001 assumes conforming input and surfaces violations only where a downstream call (TM-001) raises.
- **CFG-001 exposes no alternative options.** PTZ_SELECTION_METHOD has the single option NEAREST; FVG_INVALIDATION has the single option FIRST_TOUCH. No branching on these values is implemented, because no alternative branch exists in the specification.

---

## 3. Public API

A single entry point. Names below are interface labels for this plan; the implementation language and signature style are unconstrained by the specification, which fixes only inputs, outputs, and behaviour.
### Side Effects

None.

The function shall not modify:

- the supplied Daily candle series,
- the supplied Excluded FVG Set,
- any RawFVG object.

### `select_primary_target_zone`

**Purpose:** Perform one PTZ selection evaluation.

**Inputs:**

| Input | Description | Source spec |
|---|---|---|
| `daily_candles` | The supplied Daily OHLC series. Completed candles only, unique and strictly chronological timestamps. | DS-001 |
| `current_market_price` | The current market price. Used only for distance calculation. | TS-001 Inputs |
| `excluded_fvg_set` | A set of Daily FVG identifiers (Candle C timestamps) to exclude from selection. May be empty. Opaque — the reason for exclusion is never inspected. | TS-001 Excluded FVG Set |
| `lookback_days` | The lookback window length in calendar days. Supplied from CFG-001 (default 14). | CFG-001 |

**Output:** A `SelectionResult` (see §6) that is exactly one of:

- **PTZ found** — carries the selected RawFVG.
- **No PTZ Found** — carries no FVG; returned when the candidate pool is empty after Step 4.

**Guarantees:** stateless; deterministic for identical inputs; returns at most one PTZ per invocation.

**Non-responsibilities (by specification):** does not decide when it is invoked, does not persist or construct `excluded_fvg_set`, does not detect FVGs itself, does not determine TouchStatus itself, does not analyse lower timeframes, does not touch Points of Interest, does not execute or manage trades.

---

## 4. Internal Helper Functions

Each helper corresponds to one algorithm step or one well-defined sub-computation. Helpers are pure functions of their inputs. No helper reads configuration or clocks directly; all external values arrive as parameters.

| Helper | Responsibility | Maps to |
|---|---|---|
| `detect_candidates` | Invoke DR-001 over `daily_candles`; return the combined Bullish + Bearish RawFVG pool as a single list. | Step 1 |
| `resolve_anchor` | Identify the latest completed Daily candle — the candle bearing the newest timestamp per DS-001. | Step 2 |
| `compute_window_bounds` | From the anchor timestamp and `lookback_days`, compute the inclusive calendar-day window `[anchor − (lookback_days − 1) days, anchor]`. Anchor day included. | Step 2 |
| `in_window` | Test whether a candidate's Candle C timestamp (`RawFVG.end_time`) falls within the window, by calendar day per DS-001. | Step 2 |
| `apply_exclusions` | Remove every candidate whose identifier (Candle C timestamp) appears in `excluded_fvg_set`. | Step 3 |
| `classify_touch` | For one candidate, invoke TM-001 with the RawFVG and `daily_candles`; return TESTED / UNTESTED. | Step 4 |
| `remove_tested` | Drop every candidate classified TESTED. | Step 4 |
| `nearest_boundary_distance` | For one candidate, compute the absolute distance from `current_market_price` to the nearer of its two boundaries. Never midpoint, never far boundary. | Step 5 |
| `select_best` | Choose the minimum-distance candidate; on tie, choose the later Candle C timestamp. | Step 6 |

Design constraints on the helpers:

- `compute_window_bounds` uses the calendar-day interpretation defined by DS-001. It performs no timezone conversion (DS-001 forbids it) and derives the window purely from the supplied timestamp.
- `nearest_boundary_distance` treats both boundaries symmetrically; direction (Bullish/Bearish) does not enter the distance calculation or the ranking.
- `select_best` is total: because DS-001 guarantees unique timestamps and DR-001 yields at most one FVG per Candle C, no two candidates can share a Candle C timestamp, so the tie-break always resolves to exactly one candidate.

---

## 5. Processing Flow

The flow mirrors the seven algorithm steps of TS-001 in order. Ordering constraints from the specification are marked.

```
INPUT: daily_candles, current_market_price, excluded_fvg_set, lookback_days

Step 1 — Detect
    candidates ← detect_candidates(daily_candles)          [DR-001]
    (Bullish and Bearish form one pool)

Step 2 — Window filter                                     [Step 1 must precede Step 2]
    anchor  ← resolve_anchor(daily_candles)                [DS-001: newest timestamp]
    window  ← compute_window_bounds(anchor, lookback_days) [anchor day included]
    candidates ← [ c in candidates if in_window(c, window) ]

Step 3 — Exclusion filter                                  [must precede Step 5]
    candidates ← apply_exclusions(candidates, excluded_fvg_set)

Step 4 — Touch filter                                      [must precede Step 5]
    candidates ← remove_tested(candidates, daily_candles)  [TM-001 per candidate]

    ── If candidates is empty here → return No PTZ Found ──

Step 5 — Distance
    for each c in candidates:
        c.distance ← nearest_boundary_distance(c, current_market_price)

Step 6 — Select
    ptz ← select_best(candidates)
          (min distance; tie → later Candle C timestamp)

Step 7 — Return
    return SelectionResult(ptz)                            [at most one PTZ]
```

Ordering notes carried from the specification:

- Step 1 shall precede Step 2 — the window filters a detected pool.
- Steps 3 and 4 shall both precede Step 5 — no distance is computed for any excluded or TESTED FVG.
- Steps 3 and 4 are order-independent with respect to the result; an implementation may swap them. This plan runs exclusion before touch classification so that TM-001 is not invoked for FVGs the caller has already excluded, but this is an efficiency choice, not a correctness requirement.

The `No PTZ Found` exit is placed after Step 4 because the specification defines it as "the candidate pool is empty after Step 4." An empty pool at any earlier point simply flows through the remaining filters and produces the same empty pool at that boundary; a short-circuit is permitted but must return the identical `No PTZ Found` result.

---

## 6. Data Structures

Structures are described by their fields and invariants, not by any language binding.

### RawFVG (produced by DR-001, consumed here)

| Field | Meaning |
|---|---|
| Direction | Bullish or Bearish. Does not influence ranking. |
| Start Time | Candle A timestamp. |
| End Time | Candle C timestamp. **Serves as the FVG identifier.** |
| Upper Boundary | Per DR-001: Low(C) bullish / Low(A) bearish. |
| Lower Boundary | Per DR-001: High(A) bullish / High(C) bearish. |
| Gap Size | As produced by DR-001. Not used by TS-001 ranking. |

TS-001 does not construct RawFVG objects and does not alter their boundaries; it consumes them as detected.

### DailyCandle (per DS-001)

Fields: Timestamp, Open, High, Low, Close. Additional fields may exist and are ignored. Precondition: completed candles only, unique and strictly chronological timestamps.

### ExcludedFVGSet

An opaque set of identifiers (Candle C timestamps). Membership test only. TS-001 neither builds nor persists it and never inspects why an entry is present.

### TouchStatus (from TM-001)

Enumeration: TESTED, UNTESTED. Only UNTESTED candidates survive Step 4.

### Window

An inclusive calendar-day interval `[start_day, anchor_day]` derived from the anchor timestamp and `lookback_days`. Used solely for the `in_window` membership test.

### CandidateDistance (internal, transient)

A candidate paired with its nearest-boundary distance. Exists only between Step 5 and Step 6; not part of the public output.

### SelectionResult (output)

Exactly one of two shapes: **PTZ found** (carries one RawFVG) or **No PTZ Found** (carries none). The two are mutually exclusive and exhaustive.

---

## 7. Error Handling

TS-001 defines no error conditions of its own; its handling obligations derive entirely from its dependencies and its input contract. The plan distinguishes **raised errors** (propagate) from **defined non-error outcomes** (return normally).

### Propagated errors

| Condition | Origin | Behaviour |
|---|---|---|
| Candle C cannot be located from `RawFVG.end_time` during touch classification | TM-001 (`shall raise an error`) | Propagate. TS-001 does not suppress or reinterpret it. |
| Duplicate timestamps in the supplied series | TM-001 / DS-001 (`not permitted` / `invalid`) | Propagate as raised by the dependency. TS-001 adds no separate check. |

### Defined non-error outcomes (must NOT raise)

| Condition | Correct behaviour |
|---|---|
| No FVGs detected | Empty pool → `No PTZ Found`. |
| All candidates fall outside the window | Empty pool → `No PTZ Found`. |
| All candidates excluded | Empty pool → `No PTZ Found`. |
| All candidates TESTED | Empty pool → `No PTZ Found`. |
| `excluded_fvg_set` is empty | Normal path; no exclusions applied. |
| An identifier in `excluded_fvg_set` matches no detected FVG | No effect (per spec); not an error. |

### Explicitly out of scope

TS-001 does not validate the DS-001 data contract (completeness, chronology, uniqueness). Those are DS-001's guarantees on input. Re-validating them here would introduce behaviour the specification does not assign to TS-001. Where a violation would break a dependency, that dependency raises, and the error propagates per the table above.

A note on price precision: DS-001 forbids implicit rounding. The distance calculation compares `current_market_price` against boundary values at the precision supplied; no rounding, snapping, or epsilon tolerance is introduced. Boundary equality in touch detection is TM-001's concern, not TS-001's.

---

## 8. Unit Test Plan

Tests are organised by algorithm step and by the invariants the specification states explicitly. No test asserts behaviour the specification does not define.

### Window (Step 2)

- Candle C on the anchor day → included (anchor day is inclusive).
- Candle C exactly `lookback_days − 1` days before the anchor → included (window lower edge).
- Candle C one day beyond the lower edge → excluded.
- FVG whose Candles A/B precede the window but whose Candle C is inside → included (membership is by Candle C only).
- Non-default `lookback_days` (e.g. 7, 30) → window scales; the literal 14 is never hardcoded.
- Weekend days counted within the span (weekends included per spec).

### Exclusion (Step 3)

- Empty set → no candidate removed.
- Set containing one candidate's Candle C → exactly that candidate removed.
- Set containing an identifier matching no candidate → no effect, no error.
- Exclusion applied before distance: an excluded FVG never appears in ranking even if it would have been nearest.

### Touch filter (Step 4)

- Candidate classified TESTED by TM-001 → removed.
- Candidate classified UNTESTED → retained.
- All candidates TESTED → `No PTZ Found`.
- TM-001 raising on unlocatable Candle C → error propagates (not swallowed).

### Distance and selection (Steps 5–6)

- Two UNTESTED FVGs at different distances → nearer selected.
- Nearest boundary chosen, not midpoint or far boundary (construct a wide gap where midpoint ranking would differ).
- Direction does not affect ranking: a Bearish FVG nearer than a Bullish one is selected, and vice versa.
- **Tie-break:** two FVGs at equal nearest-boundary distance → the one with the later Candle C timestamp selected.
- Price located inside an UNTESTED gap → distance to nearer boundary computed as specified (documents current behaviour; no zero-distance special case exists in the spec).

### Output contract (Step 7)

- Exactly one PTZ returned when a survivor exists.
- `No PTZ Found` returned when the pool is empty after Step 4, for each of the four emptying causes.
- Never more than one PTZ per invocation.

### Statelessness / determinism

- Two invocations with identical inputs → identical result.
- A first invocation does not alter the result of a second with different inputs (no retained state).
- Re-invocation with the previously selected PTZ's identifier added to `excluded_fvg_set` → the next-nearest survivor (or `No PTZ Found`) is returned. This verifies the exclusion interface supports the orchestration discard loop.

### Determinism guard

- Construct a pool where a naive implementation might depend on candidate ordering; assert the result is invariant under input reordering (subject to DS-001 chronological input, this tests internal ordering assumptions in ranking and tie-break).

---

## 9. Implementation Checklist

- [ ] Single public entry point implemented; inputs exactly `daily_candles`, `current_market_price`, `excluded_fvg_set`, `lookback_days`.
- [ ] DR-001 invoked for detection; Bullish and Bearish merged into one pool. No detection logic reimplemented in TS-001.
- [ ] Anchor resolved as the newest-timestamp completed candle per DS-001.
- [ ] Window computed as inclusive `[anchor − (lookback_days − 1), anchor]`; anchor day included; `lookback_days` sourced from CFG-001, never hardcoded.
- [ ] Window membership tested on Candle C (`end_time`) only.
- [ ] Exclusion filter applied on Candle C identifier; set treated as opaque; unmatched identifiers ignored without error.
- [ ] TM-001 invoked per candidate for TouchStatus; TESTED removed; TM-001 errors propagated.
- [ ] Both exclusion and touch filters complete before any distance is computed.
- [ ] Distance measured to nearest boundary only; direction excluded from ranking.
- [ ] Selection picks minimum distance; tie broken by later Candle C timestamp.
- [ ] `No PTZ Found` returned for every empty-pool cause; never raised as an error.
- [ ] At most one PTZ returned per invocation.
- [ ] No state retained between invocations; no clock, config file, or data source read directly inside the rule (all arrive as inputs).
- [ ] No PTZ lifecycle, POI, or trade logic present anywhere in the module.
- [ ] No price rounding or tolerance introduced.
- [ ] Unit tests from §8 implemented and passing.
- [ ] Every behaviour traceable to a TS-001 clause or a named dependency; no rule or threshold introduced that the specifications do not state.

---

## Traceability note

Every element of this plan maps to a clause in the frozen TS-001 or one of its four governing specifications. Where TS-001 is deliberately abstract — the FVG identifier, the "obtain TouchStatus from TM-001" call, the "configured market data source" behind DS-001 — this plan preserves the abstraction as a named interface point rather than resolving it with an assumption. No trading rule, ranking criterion, threshold, or lifecycle behaviour has been added.


## Performance

The implementation shall perform one pass through the
candidate pool after FVG detection.

No unnecessary repeated calls to TM-001 or repeated
distance calculations shall be performed.