"""Unit tests for the DR-001 Daily Fair Value Gap detector.

Sprint: v0.7.0

Covers the DR-001 acceptance criteria and the approved implementation
decisions:
- Detects Bullish FVGs (Low(C) > High(A))
- Detects Bearish FVGs (High(C) < Low(A))
- Strict inequalities only (equality produces no gap)
- Calculates gap size and boundaries correctly
- Returns direction correctly
- Applies no additional filters (returns every valid FVG, incl. overlaps)
- Returns RawFVG objects in chronological scan order
- Returns an empty list when fewer than three candles are supplied
- Maps start_time to Candle A and end_time to Candle C (Option A)
- Does not sort, deduplicate or modify the input

DR-001 is a pure detector: it carries no Tested/Untested status, so no
such behaviour is exercised here.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from rmr.detectors.daily_fvg import detect_daily_fvgs
from rmr.models.candle import Candle
from rmr.models.raw_fvg import Direction, RawFVG

BASE = datetime(2025, 1, 1, 0, 0, 0)


def day(offset: int) -> datetime:
    """Return the BASE timestamp shifted by ``offset`` days."""
    return BASE + timedelta(days=offset)


def candle(
    offset: int,
    *,
    open_: float,
    high: float,
    low: float,
    close: float,
) -> Candle:
    """Build a Candle timestamped at BASE + offset days."""
    return Candle(
        timestamp=day(offset),
        open=open_,
        high=high,
        low=low,
        close=close,
    )


# --------------------------------------------------------------------------
# Empty / insufficient input
# --------------------------------------------------------------------------


def test_empty_input_returns_empty_list() -> None:
    assert detect_daily_fvgs([]) == []


def test_one_candle_returns_empty_list() -> None:
    c = candle(0, open_=100.0, high=110.0, low=90.0, close=105.0)
    assert detect_daily_fvgs([c]) == []


def test_two_candles_returns_empty_list() -> None:
    c0 = candle(0, open_=100.0, high=110.0, low=90.0, close=105.0)
    c1 = candle(1, open_=100.0, high=110.0, low=90.0, close=105.0)
    assert detect_daily_fvgs([c0, c1]) == []


# --------------------------------------------------------------------------
# Bullish detection (BISI): Low(C) > High(A)
# --------------------------------------------------------------------------


def _bullish_triple() -> list[Candle]:
    # A.high = 100, C.low = 105 -> Low(C) > High(A) -> bullish gap of 5.
    a = candle(0, open_=95.0, high=100.0, low=90.0, close=98.0)
    b = candle(1, open_=101.0, high=112.0, low=101.0, close=110.0)
    c = candle(2, open_=106.0, high=115.0, low=105.0, close=113.0)
    return [a, b, c]


def test_detects_bullish_fvg() -> None:
    fvgs = detect_daily_fvgs(_bullish_triple())
    assert len(fvgs) == 1
    assert fvgs[0].direction is Direction.BULLISH


def test_bullish_boundaries_and_size() -> None:
    fvg = detect_daily_fvgs(_bullish_triple())[0]
    assert fvg.upper_boundary == 105.0  # Low(C)
    assert fvg.lower_boundary == 100.0  # High(A)
    assert fvg.gap_size == 5.0  # Low(C) - High(A)


def test_bullish_timestamps_option_a() -> None:
    fvg = detect_daily_fvgs(_bullish_triple())[0]
    assert fvg.start_time == day(0)  # Candle A
    assert fvg.end_time == day(2)  # Candle C


# --------------------------------------------------------------------------
# Bearish detection (SIBI): High(C) < Low(A)
# --------------------------------------------------------------------------


def _bearish_triple() -> list[Candle]:
    # A.low = 100, C.high = 95 -> High(C) < Low(A) -> bearish gap of 5.
    a = candle(0, open_=105.0, high=110.0, low=100.0, close=102.0)
    b = candle(1, open_=98.0, high=99.0, low=88.0, close=90.0)
    c = candle(2, open_=93.0, high=95.0, low=85.0, close=88.0)
    return [a, b, c]


def test_detects_bearish_fvg() -> None:
    fvgs = detect_daily_fvgs(_bearish_triple())
    assert len(fvgs) == 1
    assert fvgs[0].direction is Direction.BEARISH


def test_bearish_boundaries_and_size() -> None:
    fvg = detect_daily_fvgs(_bearish_triple())[0]
    assert fvg.upper_boundary == 100.0  # Low(A)
    assert fvg.lower_boundary == 95.0  # High(C)
    assert fvg.gap_size == 5.0  # Low(A) - High(C)


def test_bearish_timestamps_option_a() -> None:
    fvg = detect_daily_fvgs(_bearish_triple())[0]
    assert fvg.start_time == day(0)  # Candle A
    assert fvg.end_time == day(2)  # Candle C


# --------------------------------------------------------------------------
# Strict inequality: equality produces no gap
# --------------------------------------------------------------------------


def test_bullish_equality_produces_no_gap() -> None:
    # Low(C) == High(A) == 100 -> not strictly greater -> no gap.
    a = candle(0, open_=95.0, high=100.0, low=90.0, close=98.0)
    b = candle(1, open_=101.0, high=112.0, low=101.0, close=110.0)
    c = candle(2, open_=101.0, high=115.0, low=100.0, close=113.0)
    assert detect_daily_fvgs([a, b, c]) == []


def test_bearish_equality_produces_no_gap() -> None:
    # High(C) == Low(A) == 100 -> not strictly less -> no gap.
    a = candle(0, open_=105.0, high=110.0, low=100.0, close=102.0)
    b = candle(1, open_=98.0, high=99.0, low=88.0, close=90.0)
    c = candle(2, open_=93.0, high=100.0, low=85.0, close=88.0)
    assert detect_daily_fvgs([a, b, c]) == []


def test_no_gap_when_ranges_overlap() -> None:
    # Overlapping ranges: neither bullish nor bearish condition holds.
    a = candle(0, open_=100.0, high=110.0, low=95.0, close=105.0)
    b = candle(1, open_=101.0, high=111.0, low=96.0, close=106.0)
    c = candle(2, open_=102.0, high=112.0, low=97.0, close=107.0)
    assert detect_daily_fvgs([a, b, c]) == []


# --------------------------------------------------------------------------
# No filters / multiple detections / scan order
# --------------------------------------------------------------------------


def test_returns_multiple_fvgs_in_scan_order() -> None:
    # Two overlapping windows each form a bullish gap.
    # Windows: (c0,c1,c2) and (c1,c2,c3).
    c0 = candle(0, open_=95.0, high=100.0, low=90.0, close=98.0)
    c1 = candle(1, open_=104.0, high=109.0, low=103.0, close=108.0)  # High=109
    c2 = candle(2, open_=106.0, high=113.0, low=105.0, close=111.0)  # Low=105 > 100
    c3 = candle(3, open_=112.0, high=120.0, low=111.0, close=118.0)  # Low=111 > 109
    fvgs = detect_daily_fvgs([c0, c1, c2, c3])

    assert len(fvgs) == 2
    assert all(f.direction is Direction.BULLISH for f in fvgs)
    # Chronological scan order: first window (A=c0) then second (A=c1).
    assert fvgs[0].start_time == day(0)
    assert fvgs[0].end_time == day(2)
    assert fvgs[1].start_time == day(1)
    assert fvgs[1].end_time == day(3)


def test_detects_both_directions_in_order() -> None:
    # First window bullish, a later window bearish.
    c0 = candle(0, open_=95.0, high=100.0, low=90.0, close=98.0)
    c1 = candle(1, open_=101.0, high=112.0, low=101.0, close=110.0)
    c2 = candle(2, open_=106.0, high=118.0, low=105.0, close=116.0)  # bullish: 105>100
    c3 = candle(3, open_=140.0, high=150.0, low=135.0, close=138.0)  # A' for bearish
    c4 = candle(4, open_=125.0, high=128.0, low=120.0, close=122.0)
    c5 = candle(5, open_=120.0, high=130.0, low=118.0, close=126.0)  # High=130 < 135
    fvgs = detect_daily_fvgs([c0, c1, c2, c3, c4, c5])

    directions = [f.direction for f in fvgs]
    assert Direction.BULLISH in directions
    assert Direction.BEARISH in directions
    # Bullish (window starting c0) precedes bearish (window starting c3).
    assert directions.index(Direction.BULLISH) < directions.index(
        Direction.BEARISH
    )


def test_only_one_fvg_per_window() -> None:
    # A single window can satisfy at most one direction.
    fvgs = detect_daily_fvgs(_bullish_triple())
    assert len(fvgs) == 1


def test_returns_raw_fvg_objects() -> None:
    fvgs = detect_daily_fvgs(_bullish_triple())
    assert all(isinstance(f, RawFVG) for f in fvgs)


# --------------------------------------------------------------------------
# Input integrity
# --------------------------------------------------------------------------


def test_input_list_not_modified() -> None:
    candles = _bullish_triple()
    snapshot = list(candles)
    detect_daily_fvgs(candles)
    # Same objects, same order, same length: input untouched.
    assert candles == snapshot
    assert [id(c) for c in candles] == [id(c) for c in snapshot]


def test_input_order_preserved_not_sorted() -> None:
    # The middle candle is supplied out of timestamp order, so the list is
    # NOT sorted by time: positions are [day 0, day 2, day 1].
    # The detector must scan positionally: A = position 0 (day 0),
    # C = position 2 (day 1). Had it sorted the input, C would be day 2 with
    # a different low (101) and a day-2 end_time — so the assertions below
    # distinguish positional scanning from a re-sorted scan.
    pos0 = candle(0, open_=95.0, high=100.0, low=90.0, close=98.0)  # A, high=100
    pos1 = candle(2, open_=101.0, high=112.0, low=101.0, close=110.0)  # B (day 2)
    pos2 = candle(1, open_=106.0, high=115.0, low=105.0, close=113.0)  # C, low=105
    fvgs = detect_daily_fvgs([pos0, pos1, pos2])

    assert len(fvgs) == 1
    assert fvgs[0].direction is Direction.BULLISH
    assert fvgs[0].start_time == day(0)  # Candle A = position 0
    assert fvgs[0].end_time == day(1)  # Candle C = position 2 (not sorted)
    assert fvgs[0].upper_boundary == 105.0  # Low of position-2 candle, not day 2