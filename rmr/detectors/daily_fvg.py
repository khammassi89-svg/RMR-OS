"""Daily Fair Value Gap (FVG) detector for RMR-OS.

Sprint: v0.7.0

Rule IDs implemented: DR-001.

This module implements DR-001 exactly as specified: a pure detector that
scans Daily OHLC candles and returns every valid three-candle Fair Value
Gap, both Bullish (BISI) and Bearish (SIBI).

Per the RMR-OS Constitution and the DR-001 specification, this module:

- consumes ``Candle`` objects and returns ``RawFVG`` objects;
- applies NO additional filters beyond the geometric gap condition;
- does NOT compute Tested/Untested status (touch detection is owned by
  TS-001, which is out of scope here);
- performs NO target selection, PTZ logic, configuration handling, or any
  business logic outside DR-001.

Timestamp mapping (approved, Option A): for every detected FVG the
``start_time`` is Candle A's timestamp and the ``end_time`` is Candle C's
timestamp, representing the complete three-candle structure.

The module has no external dependencies (standard library only).
"""

from __future__ import annotations

from rmr.models.candle import Candle
from rmr.models.raw_fvg import Direction, RawFVG

__all__ = ["detect_daily_fvgs"]


def detect_daily_fvgs(candles: list[Candle]) -> list[RawFVG]:
    """Detect every valid Daily Fair Value Gap in a sequence of candles.

    The detector scans every consecutive three-candle window
    ``(A, B, C) = (candles[i], candles[i + 1], candles[i + 2])`` and emits a
    ``RawFVG`` whenever the DR-001 gap condition holds:

    - Bullish (BISI): ``Low(C) > High(A)``
      -> upper = ``Low(C)``, lower = ``High(A)``, size = ``Low(C) - High(A)``
    - Bearish (SIBI): ``High(C) < Low(A)``
      -> upper = ``Low(A)``, lower = ``High(C)``, size = ``Low(A) - High(C)``

    Only strict inequalities create a gap (DR-001: imbalance > 0). No
    additional filters are applied; every valid FVG is returned. The input
    is neither sorted, deduplicated nor modified.

    Args:
        candles: The Daily candles to scan, in the order to be processed.

    Returns:
        A list of ``RawFVG`` objects in chronological scan order. Returns an
        empty list when fewer than three candles are supplied.
    """
    detected: list[RawFVG] = []

    # Fewer than three candles cannot form a three-candle FVG.
    for index in range(len(candles) - 2):
        candle_a = candles[index]
        candle_c = candles[index + 2]

        # Bullish Fair Value Gap (BISI): Low(C) > High(A).
        if candle_c.low > candle_a.high:
            detected.append(
                RawFVG(
                    direction=Direction.BULLISH,
                    start_time=candle_a.timestamp,
                    end_time=candle_c.timestamp,
                    upper_boundary=candle_c.low,
                    lower_boundary=candle_a.high,
                    gap_size=candle_c.low - candle_a.high,
                )
            )
        # Bearish Fair Value Gap (SIBI): High(C) < Low(A).
        elif candle_c.high < candle_a.low:
            detected.append(
                RawFVG(
                    direction=Direction.BEARISH,
                    start_time=candle_a.timestamp,
                    end_time=candle_c.timestamp,
                    upper_boundary=candle_a.low,
                    lower_boundary=candle_c.high,
                    gap_size=candle_a.low - candle_c.high,
                )
            )

    return detected