"""Unit tests for the Candle OHLC data model.

Sprint: v0.4.0

Covers every validation rule declared for :class:`rmr.models.candle.Candle`:
- NaN rejection on every price field
- Infinite rejection (both +inf and -inf) on every price field
- high >= open
- high >= close
- high >= low
- low <= open
- low <= close

Also verifies immutability (frozen) and the slotted layout.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime

import pytest

from rmr.models.candle import Candle

TS = datetime(2025, 1, 1, 0, 0, 0)


def make_candle(
    *,
    open_: float = 100.0,
    high: float = 110.0,
    low: float = 90.0,
    close: float = 105.0,
) -> Candle:
    """Build a valid candle, allowing individual fields to be overridden."""
    return Candle(timestamp=TS, open=open_, high=high, low=low, close=close)


# --------------------------------------------------------------------------
# Valid construction
# --------------------------------------------------------------------------


def test_valid_candle_constructs() -> None:
    candle = make_candle()
    assert candle.timestamp == TS
    assert candle.open == 100.0
    assert candle.high == 110.0
    assert candle.low == 90.0
    assert candle.close == 105.0


def test_boundary_equality_is_valid() -> None:
    # All four prices equal: every ordering rule holds with equality.
    candle = Candle(timestamp=TS, open=50.0, high=50.0, low=50.0, close=50.0)
    assert candle.high == candle.low == candle.open == candle.close == 50.0


def test_bearish_candle_is_valid() -> None:
    # open above close is legitimate (bearish); only high/low bounds matter.
    candle = make_candle(open_=108.0, close=95.0)
    assert candle.open > candle.close


# --------------------------------------------------------------------------
# Ordering validation
# --------------------------------------------------------------------------


def test_high_below_open_rejected() -> None:
    with pytest.raises(ValueError):
        make_candle(high=99.0, open_=100.0, low=90.0, close=95.0)


def test_high_below_close_rejected() -> None:
    with pytest.raises(ValueError):
        make_candle(high=104.0, open_=100.0, low=90.0, close=105.0)


def test_high_below_low_rejected() -> None:
    with pytest.raises(ValueError):
        make_candle(high=89.0, open_=88.0, low=90.0, close=88.5)


def test_low_above_open_rejected() -> None:
    with pytest.raises(ValueError):
        make_candle(low=101.0, open_=100.0, high=110.0, close=105.0)


def test_low_above_close_rejected() -> None:
    with pytest.raises(ValueError):
        make_candle(low=106.0, open_=107.0, high=110.0, close=105.0)


# --------------------------------------------------------------------------
# NaN rejection
# --------------------------------------------------------------------------

NAN = float("nan")


@pytest.mark.parametrize("field", ["open_", "high", "low", "close"])
def test_nan_rejected_on_every_field(field: str) -> None:
    kwargs = {"open_": 100.0, "high": 110.0, "low": 90.0, "close": 105.0}
    kwargs[field] = NAN
    with pytest.raises(ValueError):
        make_candle(**kwargs)


# --------------------------------------------------------------------------
# Infinite rejection
# --------------------------------------------------------------------------

POS_INF = float("inf")
NEG_INF = float("-inf")


@pytest.mark.parametrize("field", ["open_", "high", "low", "close"])
@pytest.mark.parametrize("value", [POS_INF, NEG_INF])
def test_infinite_rejected_on_every_field(field: str, value: float) -> None:
    kwargs = {"open_": 100.0, "high": 110.0, "low": 90.0, "close": 105.0}
    kwargs[field] = value
    with pytest.raises(ValueError):
        make_candle(**kwargs)


# --------------------------------------------------------------------------
# Immutability and slots
# --------------------------------------------------------------------------


def test_candle_is_frozen() -> None:
    candle = make_candle()
    with pytest.raises(dataclasses.FrozenInstanceError):
        candle.open = 1.0  # type: ignore[misc]


def test_candle_uses_slots() -> None:
    candle = make_candle()
    # A slotted class declares __slots__ and has no per-instance __dict__.
    assert hasattr(Candle, "__slots__")
    assert Candle.__slots__ == ("timestamp", "open", "high", "low", "close")
    assert not hasattr(candle, "__dict__")


# --------------------------------------------------------------------------
# Type validation
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_timestamp",
    ["2025-01-01", 1735689600, None, [], {}, date(2025, 1, 1)],
)
def test_timestamp_must_be_datetime(bad_timestamp: object) -> None:
    # A non-datetime timestamp (including a date) must raise TypeError.
    with pytest.raises(TypeError):
        Candle(
            timestamp=bad_timestamp,  # type: ignore[arg-type]
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
        )


@pytest.mark.parametrize("field", ["open_", "high", "low", "close"])
@pytest.mark.parametrize("value", ["ABC", None, [], {}])
def test_non_numeric_price_rejected_on_every_field(
    field: str, value: object
) -> None:
    # Non-numeric prices must raise TypeError before any NaN/infinity check.
    kwargs = {"open_": 100.0, "high": 110.0, "low": 90.0, "close": 105.0}
    kwargs[field] = value  # type: ignore[assignment]
    with pytest.raises(TypeError):
        make_candle(**kwargs)  # type: ignore[arg-type]