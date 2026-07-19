# RMR-OS Constitution

**Document ID:** CONST-001

**Version:** 1.1

**Status:** Approved

**Project:** Recursive Manipulation Refinement Operating System (RMR-OS)

**Owner:** Ramzi Khammassi

---

# 1. Purpose

This Constitution defines the governing principles of RMR-OS.

Every specification, data specification, Python module, detector, engine, orchestration component, backtest, AI recommendation and future development shall comply with this document.

If any document conflicts with this Constitution, the Constitution takes precedence.

---

# 2. Mission

Build the most deterministic, explainable and research-driven trading operating system possible based exclusively on the RMR methodology.

---

# 3. Core Philosophy

RMR-OS does not predict the market.

RMR-OS measures market structure.

Every trading decision shall be:

- Deterministic
- Explainable
- Repeatable
- Testable
- Auditable

Identical inputs shall always produce identical outputs.

---

# 4. Source of Truth

The official source of truth is:

1. Constitution
2. Approved Specifications
3. Shared Data Specifications
4. Rule Registry
5. Python Code

If Python behaves differently from the approved specifications, the specifications are considered correct.

---

# 5. Engineering Principles

The project follows these principles:

- Documentation First
- Rule-Driven Development
- Specification Before Implementation
- Version Controlled
- Modular Architecture
- Single Responsibility
- Test-Driven Validation
- Research Before Modification
- Deterministic Design

---

# 6. Trading Principles

The strategy shall always follow these principles.

- One Primary Target Zone
- One Trade Per Point of Interest
- Higher Timeframes define context
- Lower Timeframes refine entries
- Manipulation Clusters drive execution
- No discretionary interpretation

---

# 7. Architectural Principles

Business rules shall remain independent.

Each specification owns exactly one responsibility.

Business rules shall communicate only through their documented inputs and outputs.

Lifecycle management belongs to orchestration, not individual business rules.

Business rules shall remain stateless unless explicitly specified.

---

# 8. AI Governance

Artificial Intelligence may:

- Implement approved specifications
- Generate code
- Produce documentation
- Generate tests
- Analyse historical results
- Recommend improvements

Artificial Intelligence shall NOT:

- Invent trading rules
- Modify strategy logic
- Override approved specifications
- Change money management automatically
- Modify approved specifications without owner approval

---

# 9. Learning Engine

The Learning Engine exists only to analyse completed trades.

Its purpose is:

- Detect recurring failures
- Detect recurring strengths
- Produce research reports
- Recommend improvements

Recommendations shall never become official until approved by the project owner.

---

# 10. Version Policy

Major Version

Changes the architecture or framework.

Minor Version

Adds approved functionality without changing existing behaviour.

Patch Version

Fixes defects or documentation without changing approved business behaviour.

---

# 11. Specification Freeze

An approved specification is considered frozen once released.

Any behavioural change shall:

- Update the affected specification.
- Update dependent specifications where required.
- Be version controlled.
- Be documented in the project changelog.
- Preserve deterministic behaviour.

---

# 12. Final Principle

Every rule inside RMR-OS shall be explainable in plain English before it is implemented in Python.

If a rule cannot be explained, it cannot be coded.

The implementation shall never become the source of truth.

The specification is always the source of truth.