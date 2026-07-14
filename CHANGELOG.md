# Changelog

## v0.3.2 - Target Selection Clarifications

### Changed

- DR-001 is now a pure detector.
- Touch detection moved from DR-001 to TS-001.
- Defined wick-touch invalidation rules.
- Defined lookback window anchor.
- Defined Candle C ownership of Daily FVG creation.
- Defined nearest-boundary distance calculation.
- Added deterministic tie-breaking using the newest Candle C.
- Clarified configuration behaviour.

---

## v0.3.0 - Target Selection Specifications

### Added

- TS-001 – Primary Target Zone (PTZ) Selection
- DR-001 – Daily Fair Value Gap Detection
- CFG-001 – Primary Target Zone Configuration
- ENG-001 – Target Selection Engine Specification

All notable changes to the RMR-OS project will be documented in this file.

The format follows Semantic Versioning:

- MAJOR.MINOR.PATCH

---

## v0.3.0 - Target Selection Specifications

### Added

- TS-001 — Primary Target Zone (PTZ) Selection
- DR-001 — Daily Fair Value Gap Detection
- CFG-001 — Primary Target Zone Configuration
- ENG-001 — Target Selection Engine Specification

### Repository

- Added `docs/config`
- Added rule hierarchy (`TS`, `DR`, `CL`, `DE`, `MM`)
- Added engineering specification structure

---

## v0.2.0 - Foundation Documentation

### Added

- Constitution
- Architecture
- Glossary
- Developer Guide
- Roadmap

---

## v0.1.0 - Repository Initialization

### Added

- Initial GitHub repository
- README.md
- Initial folder structure