"""RawFVG shared data model for RMR-OS.

Sprint: v0.4.0

Rule IDs implemented: DR-001 (data model only).

This module defines the immutable data structure emitted by the DR-001
Daily Fair Value Gap detector. Per the RMR-OS Constitution and the DR-001
specification, this module:

- contains only the shared, immutable data model;
- implements NO detection logic (finding gaps within candle data is the
  DR-001 detector's responsibility, not this model's);
- implements NO Tested/Untested status (DR-001 is a pure detector and does
  not emit status; touch detection is owned by TS-001).

``gap_size`` is stored exactly as produced by the detector. This model does
not derive or recompute it from the boundaries, because that derivation is
detection logic and therefore out of scope here.

The module has no external dependencies (standard library only).
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from datetime import datetime

__all__ = ["Direction", "RawFVG"]


class Direction(enum.Enum):
    """Direction of a Fair Value Gap, as defined by DR-001.

    DR-001 supports exactly two directions: Bullish (labelled BISI) and
    Bearish (labelled SIBI).
    """

    BULLISH = "BULLISH"  # DR-001: BISI
    BEARISH = "BEARISH"  # DR-001: SIBI


@dataclass(frozen=True, slots=True)
class RawFVG:
    """An immutable Daily Fair Value Gap as detected by DR-001.

    The object is frozen (immutable) and uses ``__slots__`` for a fixed,
    memory-efficient layout. All structural validation is performed once in
    :meth:`__post_init__`; a successfully constructed ``RawFVG`` is always
    internally consistent with the invariants DR-001 guarantees.

    Attributes:
        direction: The gap direction (Bullish or Bearish).
        start_time: Timestamp marking the start of the gap.
        end_time: Timestamp marking the end of the gap.
        upper_boundary: The upper price boundary of the gap.
        lower_boundary: The lower price boundary of the gap.
        gap_size: The size of the gap, as produced by the detector.
    """

    direction: Direction
    start_time: datetime
    end_time: datetime
    upper_boundary: float
    lower_boundary: float
    gap_size: float

    def __post_init__(self) -> None:
        # --- Type validation -------------------------------------------
        if not isinstance(self.direction, Direction):
            raise TypeError(
                f"direction must be a Direction, got "
                f"{type(self.direction).__name__}"
            )
        if not isinstance(self.start_time, datetime):
            raise TypeError(
                f"start_time must be a datetime, got "
                f"{type(self.start_time).__name__}"
            )
        if not isinstance(self.end_time, datetime):
            raise TypeError(
                f"end_time must be a datetime, got "
                f"{type(self.end_time).__name__}"
            )

        # Each numeric field must be an int or float before any numeric
        # test, then finite (reject NaN and infinite values). NaN and
        # infinite values are rejected before any ordering comparison,
        # because comparisons involving NaN silently evaluate to False.
        for name, value in (
            ("upper_boundary", self.upper_boundary),
            ("lower_boundary", self.lower_boundary),
            ("gap_size", self.gap_size),
        ):
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"{name} must be an int or float, got "
                    f"{type(value).__name__}"
                )
            if math.isnan(value):
                raise ValueError(f"{name} must not be NaN")
            if math.isinf(value):
                raise ValueError(f"{name} must not be infinite")

        # --- Structural validation -------------------------------------
        # A start cannot occur after its end.
        if self.end_time < self.start_time:
            raise ValueError(
                f"end_time ({self.end_time}) must be >= "
                f"start_time ({self.start_time})"
            )

        # DR-001 defines the imbalance strictly greater than zero, so the
        # upper boundary must lie strictly above the lower boundary.
        if self.upper_boundary <= self.lower_boundary:
            raise ValueError(
                f"upper_boundary ({self.upper_boundary}) must be > "
                f"lower_boundary ({self.lower_boundary})"
            )

        # DR-001: Imbalance > 0.
        if self.gap_size <= 0:
            raise ValueError(
                f"gap_size ({self.gap_size}) must be > 0"
            )