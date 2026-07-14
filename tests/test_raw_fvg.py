"""Unit tests for the RawFVG data model (DR-001).

Sprint: v0.4.0

Covers the validation guaranteed by :class:`rmr.models.raw_fvg.RawFVG`:
- Direction must be a Direction enum member
- start_time / end_time must be datetime instances
- upper_boundary / lower_boundary / gap_size must be numeric (int or float)
- NaN and infinite rejection on every numeric field
- end_time >= start_time
- upper_boundary > lower_boundary
- gap_size > 0

Also verifies immutability (frozen), the slotted layout, and the shape of
the Direction enum.

Per DR-001 this model carries no Tested/Untested status and performs no
detection; those concerns are intentionally absent and therefore untested
here.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime

import pytest

from rmr.models.raw_fvg import Direction, RawFVG

START = datetime(2025, 1, 1, 0, 0, 0)
END = datetime(2025, 1, 3, 0, 0, 0)


def make_raw_fvg(
    *,
    direction: Direction = Direction.BULLISH,
    start_time: datetime = START,
    end_time: datetime = END,
    upper_boundary: float = 110.0,
    lower_boundary: float = 100.0,
    gap_size: float = 10.0,
) -> RawFVG:
    """Build a valid RawFVG, allowing individual fields to be overridden."""
    return RawFVG(
        direction=direction,
        start_time=start_time,
        end_time=end_time,
        upper_boundary=upper_boundary,
        lower_boundary=lower_boundary,
        gap_size=gap_size,
    )


# --------------------------------------------------------------------------
# Direction enum
# --------------------------------------------------------------------------


def test_direction_has_exactly_two_members() -> None:
    assert set(Direction) == {Direction.BULLISH, Direction.BEARISH}
    assert Direction.BULLISH.value == "BULLISH"
    assert Direction.BEARISH.value == "BEARISH"


# --------------------------------------------------------------------------
# Valid construction
# --------------------------------------------------------------------------


def test_valid_bullish_fvg_constructs() -> None:
    fvg = make_raw_fvg()
    assert fvg.direction is Direction.BULLISH
    assert fvg.start_time == START
    assert fvg.end_time == END
    assert fvg.upper_boundary == 110.0
    assert fvg.lower_boundary == 100.0
    assert fvg.gap_size == 10.0


def test_valid_bearish_fvg_constructs() -> None:
    fvg = make_raw_fvg(direction=Direction.BEARISH)
    assert fvg.direction is Direction.BEARISH


def test_integer_numeric_fields_accepted() -> None:
    fvg = make_raw_fvg(upper_boundary=110, lower_boundary=100, gap_size=10)
    assert fvg.upper_boundary == 110
    assert fvg.gap_size == 10


def test_equal_start_and_end_time_allowed() -> None:
    # end_time == start_time is permitted (end must not precede start).
    fvg = make_raw_fvg(start_time=START, end_time=START)
    assert fvg.start_time == fvg.end_time


# --------------------------------------------------------------------------
# Direction type validation
# --------------------------------------------------------------------------


@pytest.mark.parametrize("bad_direction", ["BULLISH", "bullish", 1, None, object()])
def test_direction_must_be_enum_member(bad_direction: object) -> None:
    with pytest.raises(TypeError):
        make_raw_fvg(direction=bad_direction)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Timestamp type validation
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_time", ["2025-01-01", 1735689600, None, [], {}, date(2025, 1, 1)]
)
def test_start_time_must_be_datetime(bad_time: object) -> None:
    with pytest.raises(TypeError):
        make_raw_fvg(start_time=bad_time)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_time", ["2025-01-03", 1735862400, None, [], {}, date(2025, 1, 3)]
)
def test_end_time_must_be_datetime(bad_time: object) -> None:
    with pytest.raises(TypeError):
        make_raw_fvg(end_time=bad_time)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Numeric type validation
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field", ["upper_boundary", "lower_boundary", "gap_size"]
)
@pytest.mark.parametrize("value", ["ABC", None, [], {}])
def test_non_numeric_rejected_on_every_numeric_field(
    field: str, value: object
) -> None:
    kwargs = {"upper_boundary": 110.0, "lower_boundary": 100.0, "gap_size": 10.0}
    kwargs[field] = value  # type: ignore[assignment]
    with pytest.raises(TypeError):
        make_raw_fvg(**kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# NaN rejection
# --------------------------------------------------------------------------

NAN = float("nan")


@pytest.mark.parametrize(
    "field", ["upper_boundary", "lower_boundary", "gap_size"]
)
def test_nan_rejected_on_every_numeric_field(field: str) -> None:
    kwargs = {"upper_boundary": 110.0, "lower_boundary": 100.0, "gap_size": 10.0}
    kwargs[field] = NAN
    with pytest.raises(ValueError):
        make_raw_fvg(**kwargs)


# --------------------------------------------------------------------------
# Infinite rejection
# --------------------------------------------------------------------------

POS_INF = float("inf")
NEG_INF = float("-inf")


@pytest.mark.parametrize(
    "field", ["upper_boundary", "lower_boundary", "gap_size"]
)
@pytest.mark.parametrize("value", [POS_INF, NEG_INF])
def test_infinite_rejected_on_every_numeric_field(
    field: str, value: float
) -> None:
    kwargs = {"upper_boundary": 110.0, "lower_boundary": 100.0, "gap_size": 10.0}
    kwargs[field] = value
    with pytest.raises(ValueError):
        make_raw_fvg(**kwargs)


# --------------------------------------------------------------------------
# Structural validation
# --------------------------------------------------------------------------


def test_end_time_before_start_time_rejected() -> None:
    with pytest.raises(ValueError):
        make_raw_fvg(start_time=END, end_time=START)


def test_upper_equal_to_lower_rejected() -> None:
    with pytest.raises(ValueError):
        make_raw_fvg(upper_boundary=100.0, lower_boundary=100.0, gap_size=10.0)


def test_upper_below_lower_rejected() -> None:
    with pytest.raises(ValueError):
        make_raw_fvg(upper_boundary=99.0, lower_boundary=100.0, gap_size=10.0)


def test_gap_size_zero_rejected() -> None:
    with pytest.raises(ValueError):
        make_raw_fvg(gap_size=0.0)


def test_gap_size_negative_rejected() -> None:
    with pytest.raises(ValueError):
        make_raw_fvg(gap_size=-1.0)


# --------------------------------------------------------------------------
# Immutability and slots
# --------------------------------------------------------------------------


def test_raw_fvg_is_frozen() -> None:
    fvg = make_raw_fvg()
    with pytest.raises(dataclasses.FrozenInstanceError):
        fvg.upper_boundary = 1.0  # type: ignore[misc]


def test_raw_fvg_uses_slots() -> None:
    fvg = make_raw_fvg()
    assert hasattr(RawFVG, "__slots__")
    assert RawFVG.__slots__ == (
        "direction",
        "start_time",
        "end_time",
        "upper_boundary",
        "lower_boundary",
        "gap_size",
    )
    assert not hasattr(fvg, "__dict__")