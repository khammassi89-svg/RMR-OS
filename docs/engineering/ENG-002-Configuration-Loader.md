# Engine ID

ENG-002

---

# Engine Name

Configuration Loader

---

# Status

Approved

---

# Purpose

Load, validate and provide configuration values defined by CFG-001.

The engine does not execute trading logic.

It only loads configuration and returns a validated configuration object.

---

# Inputs

config/target_selection.yaml

---

# Dependencies

CFG-001

---

# Processing Steps

1. Load target_selection.yaml.

2. Validate required keys.

3. Validate value types.

4. Validate allowed values.

5. Create immutable configuration object.

6. Return configuration object.

---

# Output

TargetSelectionConfig

---

# Engine Responsibilities

✓ Load configuration

✓ Validate configuration

✓ Reject invalid configuration

✓ Return immutable configuration object

---

# Engine Limitations

Does not:

- Detect FVG
- Select PTZ
- Execute trades
- Modify business rules
- Change configuration values