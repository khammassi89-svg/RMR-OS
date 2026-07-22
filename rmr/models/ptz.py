"""
MD-001 - Selection Result Model.

Defines the immutable output returned by TS-001.

A SelectionResult always represents exactly one outcome:

    • PTZ_FOUND
    • NO_PTZ_FOUND

The model contains no trading logic and no lifecycle state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from rmr.models.raw_fvg import RawFVG

__all__ = [
    "SelectionStatus",
    "SelectionResult",
]


class SelectionStatus(Enum):
    """
    MD-001 Selection Result status.
    """

    PTZ_FOUND = "PTZ_FOUND"
    NO_PTZ_FOUND = "NO_PTZ_FOUND"


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """
    Immutable output of TS-001.

    Invariants
    ----------
    PTZ_FOUND
        ptz is not None.

    NO_PTZ_FOUND
        ptz is None.
    """

    status: SelectionStatus
    ptz: RawFVG | None

    def __post_init__(self) -> None:
        if self.status is SelectionStatus.PTZ_FOUND and self.ptz is None:
            raise ValueError(
                "PTZ_FOUND requires a RawFVG."
            )

        if self.status is SelectionStatus.NO_PTZ_FOUND and self.ptz is not None:
            raise ValueError(
                "NO_PTZ_FOUND requires ptz=None."
            )

    @classmethod
    def ptz_found(cls, ptz: RawFVG) -> "SelectionResult":
        """
        Construct a successful PTZ selection result.
        """
        return cls(
            status=SelectionStatus.PTZ_FOUND,
            ptz=ptz,
        )

    @classmethod
    def no_ptz_found(cls) -> "SelectionResult":
        """
        Construct a 'No PTZ Found' result.
        """
        return cls(
            status=SelectionStatus.NO_PTZ_FOUND,
            ptz=None,
        )