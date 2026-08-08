"""TS-001 Primary Target Zone Selection / ENG-001 Target Selection Engine.

Rule IDs implemented: TS-001 (Primary Target Zone Selection).
Engine IDs implemented: ENG-001 (Target Selection Engine).

Implements the deterministic selection of the single Primary Target Zone
(PTZ) according to the approved TS-001 specification and the ENG-001 engine
specification.

TS-001 is a pure, stateless selection rule. For one invocation it returns
the single Daily Fair Value Gap that becomes the PTZ, or reports that none
qualifies. Per the RMR-OS Constitution, TS-001 and ENG-001, this module:

- detects candidates via DR-001 (Step 1) and never re-implements detection;
- consumes the TouchStatus classification produced by TM-001 (Step 4) and
  never determines touch status itself;
- retains no state and returns an identical result for identical inputs;
- does not decide when it is invoked, construct or persist the Excluded FVG
  Set, manage PTZ lifetime, analyse lower timeframes, or execute trades.

Selection algorithm (TS-001), in order:

1. Detect all valid Daily FVGs (Bullish and Bearish form one pool).
2. Restrict to the LOOKBACK_DAYS window anchored on the latest completed
   Daily candle; membership is by Candle C (``end_time``) only.
3. Remove candidates whose identifier appears in the Excluded FVG Set.
4. Remove candidates classified TESTED by TM-001.
5. For each survivor, compute the distance to its nearest boundary.
6. Select the smallest distance; ties are broken by the later Candle C
   timestamp. Direction never influences ranking.
7. Return the selected FVG as the PTZ, or ``No PTZ Found`` when the pool is
   empty after Step 4.

Errors raised by TM-001 (unlocatable Candle C, invalid series) propagate;
TS-001 introduces no error conditions of its own and returns ``No PTZ
Found`` rather than raising for every empty-pool cause.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from rmr.detectors.daily_fvg import detect_daily_fvgs
from rmr.engines.touch_detection import TouchDetectionEngine, TouchStatus
from rmr.models.candle import Candle
from rmr.models.ptz import SelectionResult
from rmr.models.raw_fvg import RawFVG


@dataclass(frozen=True, slots=True)
class Window:
    """
    Inclusive TS-001 lookback window.

    Both start and end timestamps are inclusive.
    """

    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class CandidateDistance:
    """
    Internal transient pairing between a candidate FVG and its
    nearest-boundary distance.

    Exists only during TS-001 Step 5 and Step 6.
    """

    candidate: RawFVG
    distance: float


def detect_candidates(daily_candles: list[Candle]) -> list[RawFVG]:
    """
    Detect all Daily Fair Value Gap candidates using DR-001.
    """
    return detect_daily_fvgs(daily_candles)


def resolve_anchor(daily_candles: list[Candle]) -> Candle:
    """
    Return the latest completed Daily candle.
    """
    return daily_candles[-1]


def compute_window_bounds(
    anchor: Candle,
    lookback_days: int,
) -> Window:
    """
    Compute the inclusive TS-001 lookback window.
    """
    window_end = anchor.timestamp
    window_start = window_end - timedelta(days=lookback_days - 1)

    return Window(
        start=window_start,
        end=window_end,
    )


def in_window(raw_fvg: RawFVG, window: Window) -> bool:
    """
    Return True if the candidate's Candle C timestamp falls within
    the inclusive TS-001 lookback window.
    """
    return window.start <= raw_fvg.end_time <= window.end


def apply_exclusions(
    candidates: list[RawFVG],
    excluded_fvg_set: set[datetime],
) -> list[RawFVG]:
    """
    Remove candidates whose Candle C timestamp appears in the
    excluded FVG set.

    The exclusion set is treated as opaque. Membership is determined
    solely by RawFVG.end_time.
    """
    return [
        candidate
        for candidate in candidates
        if candidate.end_time not in excluded_fvg_set
    ]


def classify_touch(
    touch_engine: TouchDetectionEngine,
    raw_fvg: RawFVG,
    daily_candles: list[Candle],
) -> TouchStatus:
    """
    Delegate touch classification to TM-001.

    Any exception raised by the Touch Detection Engine is
    intentionally propagated.
    """
    return touch_engine.classify(
        raw_fvg=raw_fvg,
        candles=daily_candles,
    )


def remove_tested(
    candidates: list[RawFVG],
    daily_candles: list[Candle],
) -> list[RawFVG]:
    """
    Remove every candidate classified TESTED by TM-001.

    A single TouchDetectionEngine instance is reused for the
    entire filtering pass.
    """
    touch_engine = TouchDetectionEngine()

    return [
        candidate
        for candidate in candidates
        if classify_touch(
            touch_engine,
            candidate,
            daily_candles,
        )
        is TouchStatus.UNTESTED
    ]


def nearest_boundary_distance(
    raw_fvg: RawFVG,
    current_market_price: float,
) -> CandidateDistance:
    """
    Compute the nearest-boundary distance for one candidate.

    Distance is measured to the nearer of the two FVG boundaries,
    regardless of direction.
    """
    lower_distance = abs(
        current_market_price - raw_fvg.lower_boundary
    )

    upper_distance = abs(
        current_market_price - raw_fvg.upper_boundary
    )

    return CandidateDistance(
        candidate=raw_fvg,
        distance=min(
            lower_distance,
            upper_distance,
        ),
    )


def select_best(ranked: list[CandidateDistance]) -> RawFVG:
    """Select the winning candidate (TS-001 Step 6).

    The candidate with the smallest nearest-boundary distance wins. If two
    candidates are equally near, the newer one wins, using the later Candle C
    timestamp (``end_time``). Direction never influences ranking.

    This function is total: DS-001 guarantees unique timestamps and DR-001
    yields at most one FVG per Candle C, so no two candidates can share a
    Candle C timestamp and the tie-break always resolves to exactly one
    candidate. The caller guarantees ``ranked`` is non-empty.
    """
    best = ranked[0]

    for current in ranked[1:]:
        if current.distance < best.distance:
            best = current
        elif (
            current.distance == best.distance
            and current.candidate.end_time > best.candidate.end_time
        ):
            best = current

    return best.candidate


def select_primary_target_zone(
    daily_candles: list[Candle],
    current_market_price: float,
    excluded_fvg_set: set[datetime],
    lookback_days: int,
) -> SelectionResult:
    """Perform one PTZ selection evaluation (TS-001 / ENG-001).

    Args:
        daily_candles: The supplied Daily OHLC series. Completed candles
            only, with unique and strictly chronological timestamps
            (DS-001). Not modified.
        current_market_price: The current market price, used only for the
            nearest-boundary distance calculation.
        excluded_fvg_set: Daily FVG identifiers (Candle C timestamps) to
            exclude from selection. Opaque and may be empty. Not modified.
        lookback_days: The lookback window length in calendar days, supplied
            from CFG-001 (default 14).

    Returns:
        A ``SelectionResult`` carrying exactly one PTZ, or ``No PTZ Found``
        when the candidate pool is empty after Step 4.

    Raises:
        The engine introduces no errors of its own. Errors raised by TM-001
        during touch classification (unlocatable Candle C, invalid series)
        propagate unchanged.
    """
    # Step 1 - Detect candidates (Bullish and Bearish form one pool).
    candidates = detect_candidates(daily_candles)

    # Step 2 - Restrict to the lookback window (Step 1 precedes Step 2).
    # With no candles there is no anchor and therefore no window; the pool is
    # empty and the result is No PTZ Found.
    if not daily_candles:
        return SelectionResult.no_ptz_found()

    anchor = resolve_anchor(daily_candles)
    window = compute_window_bounds(anchor, lookback_days)
    candidates = [
        candidate for candidate in candidates if in_window(candidate, window)
    ]

    # Step 3 - Remove excluded candidates (before any distance is computed).
    candidates = apply_exclusions(candidates, excluded_fvg_set)

    # Step 4 - Remove TESTED candidates via TM-001 (before any distance).
    # Exclusion is applied before touch classification so TM-001 is not
    # invoked for FVGs the caller has already excluded; this is an efficiency
    # choice permitted by the specification and does not change the result.
    candidates = remove_tested(candidates, daily_candles)

    # No PTZ Found is returned when the candidate pool is empty after Step 4.
    if not candidates:
        return SelectionResult.no_ptz_found()

    # Step 5 - Distance to the nearest boundary for each survivor.
    ranked = [
        nearest_boundary_distance(candidate, current_market_price)
        for candidate in candidates
    ]

    # Step 6 - Select the best candidate (min distance; tie -> later C).
    ptz = select_best(ranked)

    # Step 7 - Return the selected FVG as the PTZ.
    return SelectionResult.ptz_found(ptz)