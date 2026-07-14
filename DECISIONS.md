# RMR-OS Architectural Decisions

This document records approved architectural decisions made during development.

Specifications define **what** the system does.

This document records **why** specific architectural decisions were made.

---

# ADR-001 — DR-001 is a Pure Detector

Status: Approved

Decision:

The Daily Fair Value Gap detector (DR-001) is a pure geometric detector.

Responsibilities:

- Detect Bullish FVGs
- Detect Bearish FVGs
- Return RawFVG objects

Non-responsibilities:

- Tested / Untested status
- Target Selection
- PTZ
- Configuration
- Trade logic

Reason:

Keeps DR-001 single-purpose and compliant with the RMR Constitution.

---

# ADR-002 — Tested/Untested Ownership

Status: Approved

Decision:

Tested / Untested determination belongs to TS-001.

Reason:

Touch detection is part of business logic, not geometric detection.

---

# ADR-003 — RawFVG Time Mapping

Status: Approved

Decision:

RawFVG timestamps use:

- start_time = Candle A timestamp
- end_time = Candle C timestamp

Reason:

Represents the complete three-candle structure that forms the Fair Value Gap.

---

# ADR-004 — Primary Target Selection

Status: Approved

Decision:

When multiple valid Daily FVGs exist:

1. Remove Tested FVGs.
2. Measure distance to the nearest boundary.
3. Select the nearest remaining FVG.
4. If equal distance, choose the newest (latest Candle C).

Reason:

Provides deterministic selection while remaining faithful to TS-001.

---

# ADR-005 — Development Workflow

Status: Approved

Decision:

Every implementation follows:

1. Specification
2. Technical Review
3. Clarifications
4. Production Code
5. Code Review
6. Automated Tests
7. Git Commit
8. Push
9. Release (major milestones)

Reason:

Ensures deterministic, specification-driven development.