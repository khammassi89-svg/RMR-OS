# RMR-OS Architecture

**Document ID:** ARCH-001

**Version:** 1.0

**Status:** Approved

---

# Overview

RMR-OS is composed of independent modules.

Each module has a single responsibility.

Modules communicate through clearly defined inputs and outputs.

No module may modify another module's logic.

---

# System Architecture

```
                    RMR-OS
                       │
 ┌─────────────────────┼─────────────────────┐
 │                     │                     │
 ▼                     ▼                     ▼
Knowledge Base     Rule Registry      Configuration
 │                     │                     │
 └──────────────┬──────┴──────────────┬──────┘
                ▼
        Detection Engine
                │
                ▼
     Recursive Refinement Engine
                │
                ▼
        Cluster Engine
                │
                ▼
        Decision Engine
                │
                ▼
       Execution Engine
                │
                ▼
    Money Management Engine
                │
                ▼
      Backtesting Engine
                │
                ▼
       Statistics Engine
                │
                ▼
       Learning Engine
                │
                ▼
       Research Engine
                │
                ▼
          AI Advisor
```

---

# Module Responsibilities

## Knowledge Base

Stores verified concepts from the mentor's course.

---

## Rule Registry

Contains every official rule used by RMR.

---

## Detection Engine

Detects all approved technical structures.

Examples:

- Daily FVG
- FU
- BIW
- Inside Bar
- Order Block

---

## Recursive Refinement Engine

Breaks higher timeframe structures into lower timeframe structures.

---

## Cluster Engine

Groups manipulation structures into a Zone of Interest.

---

## Decision Engine

Determines whether a trade is valid.

---

## Execution Engine

Calculates:

- Entry
- Stop Loss
- Take Profit

according to the specifications.

---

## Money Management Engine

Applies:

- Risk %
- Break Even
- Trailing Stop

---

## Backtesting Engine

Executes historical simulations.

---

## Statistics Engine

Measures:

- Win Rate
- RR
- Drawdown
- Expectancy
- Trade Distribution

---

## Learning Engine

Analyses completed trades.

Detects recurring strengths and weaknesses.

Produces research recommendations.

---

## Research Engine

Runs experiments.

Compares parameters.

Produces statistical reports.

---

## AI Advisor

Uses the repository specifications and historical research to explain decisions.

The AI Advisor never invents rules.

---

# Architecture Principles

- Modular
- Deterministic
- Explainable
- Testable
- Version Controlled