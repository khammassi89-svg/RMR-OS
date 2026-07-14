# Engine ID

ENG-003

---

# Engine Name

Touch Detection Engine

---

# Status

Approved

---

# Purpose

Determine whether a detected Daily Fair Value Gap has been Tested or remains Untested.

The engine does not detect Fair Value Gaps.

It only classifies existing RawFVG objects.

---

# Inputs

RawFVG

Daily OHLC Data

---

# Dependencies

TM-001

DR-001

---

# Processing Steps

1. Receive one RawFVG.

2. Locate Candle C using RawFVG.end_time.

3. Scan every candle after Candle C in the supplied chronological Daily OHLC series.

4. Compare Candle.high and Candle.low against the Fair Value Gap boundaries as defined by TM-001.

5. If a touch is detected, return Tested.

6. Otherwise, return Untested.

---

# Output

TouchStatus

Values

- TESTED
- UNTESTED

---

# Engine Responsibilities

✓ Determine Tested status

✓ Determine Untested status

✓ Apply touch rules

✓ Return classification

---

# Engine Limitations

Does not:

- Detect FVGs
- Select PTZ
- Calculate distances
- Apply lookback filtering
- Execute trades

# Implementation Module

rmr/engines/touch_detection.py

---