# Binary Size and Execution Cost Tracker

The Binary Size and Execution Cost Tracker is a tool for monitoring and comparing the compiled binary sizes and execution costs of OpShin smart contracts across different optimization levels.

## Overview

This tool helps identify performance regressions by tracking:
- **Binary Sizes**: The size of compiled CBOR files
- **Execution Costs**: CPU and memory costs when running contracts with test inputs

## Features

- Track binary sizes across multiple optimization levels (O0, O1, O2, O3)
- Track execution costs (CPU/MEM) for specific test cases
- Compare against baseline measurements from previous releases
- Report significant changes with warnings
- Backward compatible with old baseline format
- Automatic execution in CI/CD on pull requests

## Configuration

Contracts to track are defined in `scripts/binary_size_config.yaml`:

```yaml
contracts:
  - name: "contract_name"
    path: "path/to/contract.py"
    purpose: "spending"
    description: "Description of the contract"
    extra_flags: []  # Optional compiler flags
    test_inputs:     # Optional: for execution cost tracking
      - test_case_name: "valid_input"
        inputs_hex:
          - "14"  # datum (hex-encoded CBOR)
          - "16"  # redeemer (hex-encoded CBOR)
          - "d8799f..."  # script context (hex-encoded CBOR)
```

### Adding Test Cases for Execution Cost Tracking

To track execution costs, add `test_inputs` to a contract configuration:

1. **test_case_name**: A descriptive name for the test case
2. **inputs_hex**: A list of hex-encoded CBOR values representing the contract parameters

The inputs should match the contract's expected parameters:
- For spending validators: `[datum, redeemer, script_context]`
- For minting policies: `[redeemer, script_context]`
- For other purposes: consult the contract signature

#### Getting Hex-Encoded Inputs

You can get hex-encoded CBOR inputs from existing tests:

```python
import uplc

# Example: encode an integer
datum = 20
hex_datum = uplc.PlutusInteger(datum).to_cbor().hex()

# Example: encode a PlutusData structure
from opshin.prelude import *
datum = SomeDatum(field1=value1, field2=value2)
hex_datum = datum.to_cbor().hex()
```

## Usage

### Generate Baseline

Generate a baseline file with current measurements:

```bash
python scripts/binary_size_tracker.py generate --baseline-file baseline.json
```

### Compare Against Baseline

Compare current measurements with a baseline:

```bash
python scripts/binary_size_tracker.py compare --baseline-file baseline.json
```

The script will:
1. Compile all configured contracts at each optimization level
2. Measure binary sizes
3. Evaluate contracts with test inputs (if provided) to measure execution costs
4. Compare against baseline and report changes

### CI/CD Integration

The tracker runs automatically on pull requests via `.github/workflows/binary-size-tracker.yml`:

1. Downloads baseline from latest release (or generates one from the dev branch)
2. Measures current binary sizes and execution costs
3. Compares and reports changes
4. Comments on the PR with results
5. Fails if significant changes are detected (configurable thresholds)

## Output Format

### Baseline File Structure

```json
{
  "contracts": {
    "contract_name": {
      "sizes": {
        "O1": {
          "size": 1234,
          "execution_costs": [
            {
              "test_case": "valid_input",
              "cpu": 50000000,
              "memory": 25000000
            }
          ]
        }
      },
      "path": "path/to/contract.py",
      "purpose": "spending",
      "description": "Contract description",
      "extra_flags": []
    }
  },
  "metadata": {
    "optimization_levels": ["O1", "O2", "O3"],
    "total_contracts": 1
  }
}
```

### Comparison Report

Example output:

```
======================================================================
BINARY SIZE AND EXECUTION COST COMPARISON REPORT
======================================================================

Contract: assert_sum
Description: Simple spending validator with assertion
--------------------------------------------------
  O2: 1,200 → 1,180 bytes (-20 bytes, -1.7%) ↘️ (size reduced)
    Test 'valid_sum': CPU 50,000,000 → 48,000,000 (-2,000,000, -4.0%) | MEM 25,000,000 → 24,000,000 (-1,000,000, -4.0%) ↘️ (costs reduced)

======================================================================
✅ No significant changes detected
======================================================================
```

## Thresholds

Configurable in `binary_size_config.yaml`:

```yaml
thresholds:
  warning: 5.0        # Warn if changes exceed 5%
  significant: 10.0   # Mark as significant if changes exceed 10%

ignore_warnings: ["O0", "O1"]  # Don't warn for these optimization levels
```

## Backward Compatibility

The tool supports both old and new baseline formats:

- **Old format**: Sizes are stored as integers
- **New format**: Sizes are stored as objects with optional execution_costs

This ensures existing baselines continue to work without modification.

## Adding New Contracts

To add a new contract for tracking:

1. Add an entry to `scripts/binary_size_config.yaml`:

```yaml
  - name: "my_contract"
    path: "examples/smart_contracts/my_contract.py"
    purpose: "spending"
    description: "My contract description"
```

2. Optionally add test inputs for execution cost tracking:

```yaml
    test_inputs:
      - test_case_name: "typical_usage"
        inputs_hex:
          - "..."  # datum
          - "..."  # redeemer
          - "..."  # script context
```

3. Regenerate the baseline:

```bash
python scripts/binary_size_tracker.py generate
```

## Troubleshooting

### "Failed to evaluate contract"

- Ensure test inputs are valid hex-encoded CBOR
- Check that inputs match the contract's parameter types
- Verify the contract compiles successfully

### "Could not find cost information in output"

- The eval_uplc output format may have changed
- Check that `opshin eval_uplc` is working correctly
- Verify the output contains "CPU:" and "MEM:" lines

### "No baseline found"

- Run `generate` to create a baseline first
- For CI/CD, ensure the latest release includes a baseline artifact

## Related Files

- `scripts/binary_size_tracker.py` - Main tracking script
- `scripts/binary_size_config.yaml` - Configuration file
- `.github/workflows/binary-size-tracker.yml` - CI/CD workflow
- `scripts/check_binary_sizes.py` - Legacy size checking script
