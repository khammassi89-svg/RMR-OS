"""Touch Detection Engine.

Implements
---------
TM-001  : Touch Detection (rule)
ENG-003 : Touch Detection Engine (engine specification)

Depends on
----------
DR-001  : Daily Fair Value Gap Detection (supplies ``RawFVG`` and ``Candle``)

Scope (ENG-003 / TM-001 Limitations)
------------------------------------
This module classifies an existing ``RawFVG`` as TESTED or UNTESTED.

It does not:
    - Detect FVGs
    - Select PTZ
    - Calculate distances
    - Apply lookback filtering
    - Execute trades

DR-001 is a pure detector: ``RawFVG`` carries no touch state. TouchStatus is
computed by TM-001 and returned to the caller. The classification is a pure,
deterministic function of the supplied ``RawFVG`` and the supplied
chronological Daily OHLC series. ``RawFVG`` is never modified.
"""

from __future__ import annotations

from enum import Enum
from typing import Sequence

from rmr.models.candle import Candle
from rmr.models.raw_fvg import RawFVG

__all__ = [
    "TouchStatus",
    "TouchDetectionError",
    "CandleCNotFoundError",
    "InvalidCandleSeriesError",
    "TouchDetectionEngine",
]


class TouchStatus(Enum):
    """TM-001 Output.

    Values are defined by TM-001 and are the only permitted results.
    """

    TESTED = "TESTED"
    UNTESTED = "UNTESTED"


class TouchDetectionError(Exception):
    """Base error raised by the Touch Detection Engine (ENG-003)."""


class CandleCNotFoundError(TouchDetectionError):
    """Candle C could not be located using ``RawFVG.end_time``.

    TM-001 Input Requirements:
        "If Candle C cannot be located using RawFVG.end_time, the engine
        shall raise an error."
    """


class InvalidCandleSeriesError(TouchDetectionError):
    """The supplied Daily OHLC series violates TM-001 Input Requirements.

    TM-001 Input Requirements:
        - The supplied Daily OHLC candle series must be in chronological order.
        - Duplicate timestamps are not permitted.
    """


class TouchDetectionEngine:
    """ENG-003 - Touch Detection Engine.

    Stateless. Classifies one ``RawFVG`` per call against a supplied
    chronological Daily OHLC series and returns the resulting TouchStatus.
    """

    def classify(self, raw_fvg: RawFVG, candles: Sequence[Candle]) -> TouchStatus:
        """Return the TM-001 ``TouchStatus`` of ``raw_fvg``.

        Processing Rules (TM-001 / ENG-003):
            1. Receive one RawFVG.
            2. Locate Candle C using RawFVG.end_time.
            3. Scan every candle after Candle C.
            4. Compare Candle.high and Candle.low against the gap boundaries.
            5. If any candle touches the gap, return TESTED.
            6. Otherwise, return UNTESTED.

        Args:
            raw_fvg: A Fair Value Gap produced by DR-001. Read only; never
                modified by this engine.
            candles: Daily OHLC candles in chronological order, without
                duplicate timestamps. The series must contain Candle C.

        Returns:
            ``TouchStatus.TESTED`` or ``TouchStatus.UNTESTED``.

        Raises:
            InvalidCandleSeriesError: The series is not in chronological order
                or contains duplicate timestamps.
            CandleCNotFoundError: Candle C could not be located using
                ``raw_fvg.end_time``.
        """
        self._validate_series(candles)
        index_c = self._locate_candle_c(raw_fvg, candles)

        # TM-001: "Candles A, B and C are never evaluated."
        # "After Candle C" means every candle whose position follows
        # Candle C in the supplied series.
        for candle in candles[index_c + 1 :]:
            if self.is_touch(candle, raw_fvg):
                # TM-001: "The first touch permanently changes the status
                # to Tested." Scanning stops at the first touch.
                return TouchStatus.TESTED

        return TouchStatus.UNTESTED

    @staticmethod
    def is_touch(candle: Candle, raw_fvg: RawFVG) -> bool:
        """Apply the TM-001 Touch Definition to a single candle.

        TM-001:
            Candle.high >= RawFVG.lower_boundary
            AND
            Candle.low  <= RawFVG.upper_boundary

        Both gap boundaries are inclusive. A candle close is not required;
        the wick alone is sufficient.
        """
        return (
            candle.high >= raw_fvg.lower_boundary
            and candle.low <= raw_fvg.upper_boundary
        )

    @staticmethod
    def _validate_series(candles: Sequence[Candle]) -> None:
        """Enforce the TM-001 Input Requirements on the supplied series.

        TM-001 requires the series to be chronological and free of duplicate
        timestamps. Both are enforced by requiring strictly increasing
        timestamps, which also guarantees that Candle C resolves to exactly
        one position.
        """
        for previous, current in zip(candles, candles[1:]):
            if current.timestamp == previous.timestamp:
                raise InvalidCandleSeriesError(
                    f"Duplicate timestamp in Daily OHLC series: {current.timestamp!r}."
                )
            if current.timestamp < previous.timestamp:
                raise InvalidCandleSeriesError(
                    "Daily OHLC series is not in chronological order: "
                    f"{current.timestamp!r} follows {previous.timestamp!r}."
                )

    @staticmethod
    def _locate_candle_c(raw_fvg: RawFVG, candles: Sequence[Candle]) -> int:
        """Return the position of Candle C, identified by ``RawFVG.end_time``."""
        for index, candle in enumerate(candles):
            if candle.timestamp == raw_fvg.end_time:
                return index

        raise CandleCNotFoundError(
            "Candle C could not be located in the supplied Daily OHLC series "
            f"using RawFVG.end_time={raw_fvg.end_time!r}."
        )