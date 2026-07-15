"""Test suite for TM-001 - Touch Detection / ENG-003 - Touch Detection Engine.

Every test maps to a clause of TM-001 or ENG-003. No behaviour is asserted
that is not stated in an approved specification.

DR-001 binding
--------------
``Candle`` and ``RawFVG`` are imported from the DR-001 detector module and are
never modified by this suite. DR-001 is a pure detector: ``RawFVG`` carries no
touch state, so TouchStatus is only ever obtained as the return value of
TM-001. The factories below (``make_candle`` / ``make_fvg``) are the single
place where this suite binds to the DR-001 definitions.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from rmr.detectors.daily_fvg import Candle, Direction, RawFVG
from rmr.engines.touch_detection import (
    CandleCNotFoundError,
    InvalidCandleSeriesError,
    TouchDetectionEngine,
    TouchStatus,
)

DAY_0 = datetime(2025, 1, 1)


def day(offset: int) -> datetime:
    """Return the Daily timestamp for ``offset`` days after DAY_0."""
    return DAY_0 + timedelta(days=offset)


def make_candle(
    offset: int,
    high: float,
    low: float,
    *,
    timestamp: datetime | None = None,
) -> Candle:
    """Build a Daily candle.

    Only ``timestamp``, ``high`` and ``low`` are consumed by TM-001;
    ``open`` and ``close`` are populated with valid in-range values so the
    tests never rely on them.
    """
    mid = (high + low) / 2
    return Candle(
        timestamp=day(offset) if timestamp is None else timestamp,
        open=mid,
        high=high,
        low=low,
        close=mid,
    )


def make_fvg(
    *,
    upper_boundary: float,
    lower_boundary: float,
    start_offset: int = 0,
    end_offset: int = 2,
    direction: Direction = Direction.BULLISH,
) -> RawFVG:
    """Build a DR-001 RawFVG whose Candle C sits at ``end_offset``."""
    return RawFVG(
        direction=direction,
        start_time=day(start_offset),
        end_time=day(end_offset),
        upper_boundary=upper_boundary,
        lower_boundary=lower_boundary,
        gap_size=upper_boundary - lower_boundary,
    )


@pytest.fixture
def engine() -> TouchDetectionEngine:
    return TouchDetectionEngine()


@pytest.fixture
def gap() -> RawFVG:
    """A gap spanning 100.0 - 110.0 with Candle C at day 2."""
    return make_fvg(upper_boundary=110.0, lower_boundary=100.0)


def series_through_candle_c() -> list[Candle]:
    """Candles A, B and C. All three sit inside the 100.0 - 110.0 gap."""
    return [
        make_candle(0, high=105.0, low=101.0),
        make_candle(1, high=109.0, low=100.5),
        make_candle(2, high=108.0, low=102.0),
    ]


# ---------------------------------------------------------------------------
# TM-001 Output
# ---------------------------------------------------------------------------


class TestTouchStatus:
    """TM-001 Output: TouchStatus values are TESTED and UNTESTED."""

    def test_touch_status_defines_exactly_two_values(self) -> None:
        assert {status.name for status in TouchStatus} == {"TESTED", "UNTESTED"}

    def test_touch_status_is_owned_by_tm001_not_by_raw_fvg(
        self, gap: RawFVG
    ) -> None:
        # DR-001 is a pure detector: RawFVG carries no touch state.
        assert not hasattr(gap, "status")


# ---------------------------------------------------------------------------
# TM-001 Touch Definition
# ---------------------------------------------------------------------------


class TestTouchDefinition:
    """TM-001 Touch Definition.

    Candle.high >= lower_boundary AND Candle.low <= upper_boundary.
    Both boundaries are inclusive.
    """

    def test_candle_fully_inside_the_gap_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=108.0, low=102.0)]
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    def test_candle_engulfing_the_gap_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=130.0, low=80.0)]
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    def test_candle_entering_the_gap_from_above_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=120.0, low=109.0)]
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    def test_candle_entering_the_gap_from_below_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=101.0, low=90.0)]
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    def test_candle_entirely_above_the_gap_is_untested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=125.0, low=110.01)]
        assert engine.classify(gap, candles) is TouchStatus.UNTESTED

    def test_candle_entirely_below_the_gap_is_untested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=99.99, low=90.0)]
        assert engine.classify(gap, candles) is TouchStatus.UNTESTED


class TestBoundaryInclusivity:
    """TM-001: "Equality with either boundary counts as a touch." """

    def test_high_equal_to_lower_boundary_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=100.0, low=90.0)]
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    def test_low_equal_to_upper_boundary_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=120.0, low=110.0)]
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    def test_candle_touching_both_boundaries_exactly_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=110.0, low=100.0)]
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    @pytest.mark.parametrize(
        ("high", "low", "expected"),
        [
            (99.99, 95.0, TouchStatus.UNTESTED),  # just below lower boundary
            (100.0, 95.0, TouchStatus.TESTED),  # exactly on lower boundary
            (100.01, 95.0, TouchStatus.TESTED),  # just inside lower boundary
            (115.0, 110.01, TouchStatus.UNTESTED),  # just above upper boundary
            (115.0, 110.0, TouchStatus.TESTED),  # exactly on upper boundary
            (115.0, 109.99, TouchStatus.TESTED),  # just inside upper boundary
        ],
    )
    def test_boundary_transitions(
        self,
        engine: TouchDetectionEngine,
        gap: RawFVG,
        high: float,
        low: float,
        expected: TouchStatus,
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=high, low=low)]
        assert engine.classify(gap, candles) is expected


class TestCloseIsNotRequired:
    """TM-001: "A candle close is not required." """

    def test_wick_touch_with_body_outside_the_gap_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        wick_only = Candle(
            timestamp=day(3),
            open=120.0,
            high=121.0,
            low=105.0,  # wick enters the gap
            close=119.0,  # body stays entirely above the gap
        )
        candles = series_through_candle_c() + [wick_only]
        assert engine.classify(gap, candles) is TouchStatus.TESTED


# ---------------------------------------------------------------------------
# TM-001 Scan Window
# ---------------------------------------------------------------------------


class TestScanWindow:
    """TM-001: "Candles A, B and C are never evaluated." """

    def test_candles_a_b_and_c_inside_the_gap_do_not_test_it(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        # Candles A, B and C all trade inside 100.0 - 110.0.
        assert engine.classify(gap, series_through_candle_c()) is TouchStatus.UNTESTED

    def test_candles_before_candle_a_are_not_evaluated(
        self, engine: TouchDetectionEngine
    ) -> None:
        fvg = make_fvg(
            upper_boundary=110.0, lower_boundary=100.0, start_offset=1, end_offset=3
        )
        candles = [
            make_candle(0, high=115.0, low=95.0),  # engulfs the gap, but precedes it
            make_candle(1, high=98.0, low=90.0),
            make_candle(2, high=99.0, low=91.0),
            make_candle(3, high=125.0, low=111.0),
        ]
        assert engine.classify(fvg, candles) is TouchStatus.UNTESTED

    def test_candle_c_being_the_last_candle_is_untested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        assert engine.classify(gap, series_through_candle_c()) is TouchStatus.UNTESTED

    def test_only_candles_after_candle_c_are_evaluated(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [
            make_candle(3, high=98.0, low=90.0),
            make_candle(4, high=99.5, low=92.0),
        ]
        assert engine.classify(gap, candles) is TouchStatus.UNTESTED


class TestFirstTouch:
    """TM-001: "The first touch permanently changes the status to Tested." """

    def test_touch_followed_by_price_leaving_the_gap_remains_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [
            make_candle(3, high=105.0, low=101.0),  # touch
            make_candle(4, high=150.0, low=140.0),  # far above
            make_candle(5, high=160.0, low=150.0),  # far above
        ]
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    def test_late_touch_after_many_untouching_candles_is_tested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c()
        candles += [make_candle(offset, high=90.0, low=80.0) for offset in range(3, 20)]
        candles.append(make_candle(20, high=100.0, low=95.0))  # touches lower boundary
        assert engine.classify(gap, candles) is TouchStatus.TESTED

    def test_no_touching_candle_after_candle_c_is_untested(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c()
        candles += [make_candle(offset, high=99.0, low=80.0) for offset in range(3, 20)]
        assert engine.classify(gap, candles) is TouchStatus.UNTESTED


# ---------------------------------------------------------------------------
# TM-001 Direction independence
# ---------------------------------------------------------------------------


class TestDirectionIndependence:
    """TM-001 defines one touch rule; it does not branch on direction."""

    @pytest.mark.parametrize("direction", [Direction.BULLISH, Direction.BEARISH])
    def test_touch_is_classified_identically_for_both_directions(
        self, engine: TouchDetectionEngine, direction: Direction
    ) -> None:
        fvg = make_fvg(upper_boundary=110.0, lower_boundary=100.0, direction=direction)
        candles = series_through_candle_c() + [make_candle(3, high=105.0, low=95.0)]
        assert engine.classify(fvg, candles) is TouchStatus.TESTED

    @pytest.mark.parametrize("direction", [Direction.BULLISH, Direction.BEARISH])
    def test_no_touch_is_classified_identically_for_both_directions(
        self, engine: TouchDetectionEngine, direction: Direction
    ) -> None:
        fvg = make_fvg(upper_boundary=110.0, lower_boundary=100.0, direction=direction)
        candles = series_through_candle_c() + [make_candle(3, high=99.0, low=95.0)]
        assert engine.classify(fvg, candles) is TouchStatus.UNTESTED


# ---------------------------------------------------------------------------
# TM-001 Input Requirements
# ---------------------------------------------------------------------------


class TestCandleCLocation:
    """TM-001: "If Candle C cannot be located using RawFVG.end_time,
    the engine shall raise an error." """

    def test_missing_candle_c_raises(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = [
            make_candle(0, high=105.0, low=101.0),
            make_candle(1, high=109.0, low=100.5),
            make_candle(3, high=105.0, low=101.0),  # Candle C (day 2) absent
        ]
        with pytest.raises(CandleCNotFoundError):
            engine.classify(gap, candles)

    def test_empty_series_raises(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        with pytest.raises(CandleCNotFoundError):
            engine.classify(gap, [])

    def test_candle_c_is_located_by_end_time_not_by_position(
        self, engine: TouchDetectionEngine
    ) -> None:
        # Candle C sits at day 5; earlier candles inside the gap must be ignored.
        fvg = make_fvg(
            upper_boundary=110.0, lower_boundary=100.0, start_offset=3, end_offset=5
        )
        candles = [
            make_candle(0, high=105.0, low=101.0),  # inside the gap, before Candle A
            make_candle(1, high=105.0, low=101.0),  # inside the gap, before Candle A
            make_candle(2, high=105.0, low=101.0),  # inside the gap, before Candle A
            make_candle(3, high=99.0, low=90.0),  # Candle A
            make_candle(4, high=98.0, low=91.0),  # Candle B
            make_candle(5, high=120.0, low=111.0),  # Candle C
            make_candle(6, high=115.0, low=112.0),  # after C, no touch
        ]
        assert engine.classify(fvg, candles) is TouchStatus.UNTESTED


class TestSeriesValidation:
    """TM-001 Input Requirements: chronological order, no duplicate timestamps."""

    def test_duplicate_timestamps_raise(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [
            make_candle(3, high=98.0, low=90.0),
            make_candle(3, high=97.0, low=91.0),  # duplicate timestamp
        ]
        with pytest.raises(InvalidCandleSeriesError):
            engine.classify(gap, candles)

    def test_duplicate_candle_c_timestamp_raises(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = [
            make_candle(0, high=105.0, low=101.0),
            make_candle(1, high=109.0, low=100.5),
            make_candle(2, high=108.0, low=102.0),  # Candle C
            make_candle(2, high=108.0, low=102.0),  # duplicate Candle C
        ]
        with pytest.raises(InvalidCandleSeriesError):
            engine.classify(gap, candles)

    def test_non_chronological_series_raises(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [
            make_candle(4, high=98.0, low=90.0),
            make_candle(3, high=97.0, low=91.0),  # out of order
        ]
        with pytest.raises(InvalidCandleSeriesError):
            engine.classify(gap, candles)

    def test_reversed_series_raises(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        with pytest.raises(InvalidCandleSeriesError):
            engine.classify(gap, list(reversed(series_through_candle_c())))

    def test_single_candle_series_is_not_rejected_by_ordering(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        # Candle C only: valid series, nothing after C.
        assert engine.classify(gap, [make_candle(2, high=108.0, low=102.0)]) is (
            TouchStatus.UNTESTED
        )


# ---------------------------------------------------------------------------
# ENG-003 Engine Responsibilities and Limitations
# ---------------------------------------------------------------------------


class TestEngineContract:
    """ENG-003: the engine classifies only. RawFVG must never be modified."""

    def test_classify_returns_a_touch_status(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        result = engine.classify(gap, series_through_candle_c())
        assert isinstance(result, TouchStatus)

    def test_classify_does_not_modify_the_raw_fvg(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        before = (
            gap.direction,
            gap.start_time,
            gap.end_time,
            gap.upper_boundary,
            gap.lower_boundary,
            gap.gap_size,
        )
        candles = series_through_candle_c() + [make_candle(3, high=105.0, low=101.0)]

        assert engine.classify(gap, candles) is TouchStatus.TESTED
        assert (
            gap.direction,
            gap.start_time,
            gap.end_time,
            gap.upper_boundary,
            gap.lower_boundary,
            gap.gap_size,
        ) == before

    def test_classify_adds_no_attributes_to_the_raw_fvg(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=105.0, low=101.0)]

        engine.classify(gap, candles)

        assert not hasattr(gap, "status")
        assert not hasattr(gap, "touch_status")

    def test_classify_does_not_modify_the_candle_series(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=105.0, low=101.0)]
        snapshot = list(candles)

        engine.classify(gap, candles)

        assert candles == snapshot

    def test_repeated_classification_is_deterministic(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        candles = series_through_candle_c() + [make_candle(3, high=105.0, low=101.0)]
        results = {engine.classify(gap, candles) for _ in range(5)}
        assert results == {TouchStatus.TESTED}

    def test_classifying_the_same_fvg_twice_is_independent(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        # No touch state is carried on the RawFVG, so a TESTED result must not
        # leak into a later classification against a different series.
        touching = series_through_candle_c() + [make_candle(3, high=105.0, low=101.0)]
        not_touching = series_through_candle_c() + [make_candle(3, high=99.0, low=90.0)]

        assert engine.classify(gap, touching) is TouchStatus.TESTED
        assert engine.classify(gap, not_touching) is TouchStatus.UNTESTED

    def test_is_touch_applies_the_boundary_rule_directly(
        self, engine: TouchDetectionEngine, gap: RawFVG
    ) -> None:
        assert engine.is_touch(make_candle(9, high=100.0, low=90.0), gap) is True
        assert engine.is_touch(make_candle(9, high=99.99, low=90.0), gap) is False