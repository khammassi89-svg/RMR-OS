"""
TS-001 Primary Target Zone Selection Engine.

Implements the deterministic selection of the Primary Target Zone (PTZ)
according to the approved TS-001 specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from rmr.detectors.daily_fvg import detect_daily_fvgs
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


def detect_candidates(daily_candles: list[Candle]) -> list[RawFVG]:
    """
    Detect all Daily Fair Value Gap candidates using DR-001.

    This helper delegates detection entirely to the DR-001 detector.
    It performs no filtering or additional processing.
    """
    return detect_daily_fvgs(daily_candles)


def resolve_anchor(daily_candles: list[Candle]) -> Candle:
    """
    Return the latest completed Daily candle.

    Per DS-001, the supplied candle series is already guaranteed to
    contain completed candles in strict chronological order.
    Therefore, the anchor is simply the final candle.
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


def select_primary_target_zone(
    daily_candles: list[Candle],
    current_market_price: float,
    excluded_fvg_set,
    lookback_days: int,
):
    """
    Select the Primary Target Zone according to TS-001.
    """
    raise NotImplementedError