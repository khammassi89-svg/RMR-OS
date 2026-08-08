"""TM-001 Touch Detection / ENG-003 Touch Detection Engine.

Rule IDs implemented: TM-001 (Touch Detection).
Engine IDs implemented: ENG-003 (Touch Detection Engine).

This module classifies an existing Daily Fair Value Gap (``RawFVG``) as
TESTED or UNTESTED. Per the RMR-OS Constitution, TM-001 and ENG-003, this
module:

- consumes a ``RawFVG`` produced by DR-001 and a chronological series of
  Daily ``Candle`` objects;
- performs NO detection (finding gaps is DR-001's responsibility);
- performs NO target selection, distance calculation, lookback filtering,
  trade execution or lifecycle management (those belong to TS-001 and later
  engines);
- retains no state: a ``RawFVG`` carries no touch status, so the
  classification is only ever the return value of :meth:`classify`.

Touch definition (TM-001)
-------------------------
A Daily FVG becomes TESTED when the wick of any completed Daily candle that
occurs *after Candle C* touches or enters the gap. A candle close is not
required and equality with either boundary counts as a touch. Candles A, B
and C are never evaluated. A candle touches the gap when::

    candle.high >= raw_fvg.lower_boundary
    AND
    candle.low  <= raw_fvg.upper_boundary

Both gap boundaries are inclusive.

Input requirements (TM-001 / DS-001)
------------------------------------
The supplied Daily series shall be in strictly chronological order with
unique timestamps (DS-001). Candle C is located by ``RawFVG.end_time`` and
"after Candle C" is interpreted by position within the supplied series. If
Candle C cannot be located, the engine raises an error.

The module depends only on the shared data models (standard library aside).
"""

from __future__ import annotations

import enum

from rmr.models.candle import Candle
from rmr.models.raw_fvg import RawFVG

__all__ = [
    "TouchStatus",
    "TouchDetectionError",
    "CandleCNotFoundError",
    "InvalidCandleSeriesError",
    "TouchDetectionEngine",
]


class TouchStatus(enum.Enum):
    """TM-001 output classification.

    TM-001 defines exactly two values: a gap is either TESTED or UNTESTED.
    """

    TESTED = "TESTED"
    UNTESTED = "UNTESTED"


class TouchDetectionError(Exception):
    """Base class for every error raised by the Touch Detection Engine."""


class CandleCNotFoundError(TouchDetectionError):
    """Raised when Candle C cannot be located using ``RawFVG.end_time``.

    TM-001 Input Requirements: "If Candle C cannot be located using
    ``RawFVG.end_time``, the engine shall raise an error."
    """


class InvalidCandleSeriesError(TouchDetectionError):
    """Raised when the supplied Daily series violates DS-001.

    DS-001 requires candle timestamps to be strictly chronological and
    unique; duplicate timestamps are invalid. Either violation is reported
    through this error.
    """


class TouchDetectionEngine:
    """ENG-003 engine that classifies a ``RawFVG`` as TESTED or UNTESTED.

    The engine is stateless. It never mutates the supplied ``RawFVG`` or the
    supplied candle series, and two invocations with identical inputs always
    produce an identical result.
    """

    def classify(
        self,
        raw_fvg: RawFVG,
        candles: list[Candle],
    ) -> TouchStatus:
        """Classify one ``RawFVG`` against the supplied Daily series.

        Processing order (TM-001):

        1. Validate the series (DS-001: strictly chronological, unique
           timestamps). A violation raises ``InvalidCandleSeriesError``.
        2. Locate Candle C by ``RawFVG.end_time``. If absent, raise
           ``CandleCNotFoundError``.
        3. Scan every candle whose position follows Candle C. The first
           candle that touches the gap yields ``TESTED``; if none touches,
           the result is ``UNTESTED``.

        Args:
            raw_fvg: The Daily Fair Value Gap to classify.
            candles: The Daily candle series, in chronological order.

        Returns:
            ``TouchStatus.TESTED`` or ``TouchStatus.UNTESTED``.

        Raises:
            InvalidCandleSeriesError: The series is not strictly
                chronological or contains duplicate timestamps.
            CandleCNotFoundError: Candle C could not be located.
        """
        self._validate_series(candles)

        candle_c_index = self._locate_candle_c(raw_fvg, candles)

        # "After Candle C" is every candle whose position follows Candle C.
        # Candles A, B and C are never evaluated.
        for candle in candles[candle_c_index + 1:]:
            if self.is_touch(candle, raw_fvg):
                # The first touch permanently changes the status to TESTED.
                return TouchStatus.TESTED

        return TouchStatus.UNTESTED

    def is_touch(self, candle: Candle, raw_fvg: RawFVG) -> bool:
        """Return whether a single candle touches the gap (TM-001 rule).

        Both boundaries are inclusive: equality with either boundary counts
        as a touch. Direction is never consulted.
        """
        return (
            candle.high >= raw_fvg.lower_boundary
            and candle.low <= raw_fvg.upper_boundary
        )

    @staticmethod
    def _validate_series(candles: list[Candle]) -> None:
        """Enforce the DS-001 series contract.

        Timestamps must be strictly increasing. A strictly increasing check
        rejects both non-chronological ordering and duplicate timestamps in
        a single pass.
        """
        for previous, current in zip(candles, candles[1:]):
            if current.timestamp <= previous.timestamp:
                raise InvalidCandleSeriesError(
                    "Daily candle timestamps must be strictly chronological "
                    "and unique; "
                    f"{current.timestamp} does not follow "
                    f"{previous.timestamp}."
                )

    @staticmethod
    def _locate_candle_c(raw_fvg: RawFVG, candles: list[Candle]) -> int:
        """Return the position of Candle C, identified by ``end_time``.

        DS-001 guarantees unique timestamps, so at most one candle matches.
        """
        for index, candle in enumerate(candles):
            if candle.timestamp == raw_fvg.end_time:
                return index

        raise CandleCNotFoundError(
            f"Candle C with end_time {raw_fvg.end_time} was not found in the "
            "supplied Daily candle series."
        )