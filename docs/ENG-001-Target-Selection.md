# Engine ID

ENG-001

---

# Engine Name

Target Selection Engine

---

# Status

Approved

---

# Purpose

Determine the single Primary Target Zone (PTZ) that will be used during the current trading day.

The engine does not execute trades.

It only selects the Daily Fair Value Gap that becomes the PTZ.

---

# Inputs

Daily OHLC Data

Current Market Price

---

# Dependencies

CFG-001

DR-001

TS-001

---

# Processing Steps

1. Load Daily candles.

2. Scan previous LOOKBACK_DAYS.

3. Detect every Daily FVG.

4. Remove tested FVGs.

5. Calculate distance from current price.

6. Rank remaining FVGs.

7. Select nearest FVG.

8. Return PTZ.

---

# Output

Primary Target Zone

or

No PTZ Found

---

# Engine Responsibilities

✓ Detect candidates

✓ Validate candidates

✓ Rank candidates

✓ Return one PTZ

---

# Engine Limitations

Does not:

- Detect FU
- Detect BIW
- Detect IB
- Enter trades
- Calculate Stop Loss
- Calculate Take Profit

Those responsibilities belong to later engines.