"""
TS-001 Primary Target Zone Selection Engine.

Implements the deterministic selection of the Primary Target Zone (PTZ)
according to the approved TS-001 specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from rmr.detectors.daily_fvg import detect_daily_fvgs
from rmr.engines.touch_detection import TouchDetectionEngine, TouchStatus
from rmr.models.candle import Candle
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


def select_primary_target_zone(
    daily_candles: list[Candle],
    current_market_price: float,
    excluded_fvg_set: set[datetime],
    lookback_days: int,
):
    """
    Select the Primary Target Zone according to TS-001.
    """
    raise NotImplementedError