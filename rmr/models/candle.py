"""Candle OHLC data model for RMR-OS.

Sprint: v0.4.0

Rule IDs implemented: None.

This module is a shared, foundational data model. Per the RMR-OS
Constitution it contains no business logic, no FVG logic and no detector
logic. Its only responsibility is to represent a single, immutable Daily
OHLC candle and to reject structurally invalid input at construction time.

The module has no external dependencies (standard library only).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

__all__ = ["Candle"]


@dataclass(frozen=True, slots=True)
class Candle:
    """An immutable single OHLC candle.

    The candle is frozen (immutable) and uses ``__slots__`` for a fixed,
    memory-efficient layout. All structural validation is performed once in
    :meth:`__post_init__`; a successfully constructed ``Candle`` is always
    internally consistent.

    Attributes:
        timestamp: The candle's timestamp.
        open: The opening price.
        high: The highest price.
        low: The lowest price.
        close: The closing price.
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        # timestamp must be a real datetime instance.
        if not isinstance(self.timestamp, datetime):
            raise TypeError(
                f"timestamp must be a datetime, got {type(self.timestamp).__name__}"
            )

        # Each price must be numeric (int or float) before any numeric test,
        # then finite (reject NaN and infinite values). NaN and infinite
        # values are rejected before any ordering comparison, because
        # comparisons involving NaN silently evaluate to False.
        for name, value in (
            ("open", self.open),
            ("high", self.high),
            ("low", self.low),
            ("close", self.close),
        ):
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"{name} must be an int or float, got {type(value).__name__}"
                )
            if math.isnan(value):
                raise ValueError(f"{name} must not be NaN")
            if math.isinf(value):
                raise ValueError(f"{name} must not be infinite")

        # Ordering constraints.
        if self.high < self.open:
            raise ValueError(
                f"high ({self.high}) must be >= open ({self.open})"
            )
        if self.high < self.close:
            raise ValueError(
                f"high ({self.high}) must be >= close ({self.close})"
            )
        if self.high < self.low:
            raise ValueError(
                f"high ({self.high}) must be >= low ({self.low})"
            )
        if self.low > self.open:
            raise ValueError(
                f"low ({self.low}) must be <= open ({self.open})"
            )
        if self.low > self.close:
            raise ValueError(
                f"low ({self.low}) must be <= close ({self.close})"
            )