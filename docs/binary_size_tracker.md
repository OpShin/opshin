# Binary Size Tracker

OpShin includes a binary size tracking system to monitor changes in compiled contract sizes across different optimization levels. This helps detect regressions that could impact deployment costs and execution limits.

## Overview

The binary size tracker:
- Compiles a set of representative contracts with different optimization levels
- Measures the size of generated CBOR files (the actual on-chain binary)
- Compares current sizes against baseline measurements from the latest release
- Reports significant changes in pull requests and CI builds

## Tracked Contracts

The system tracks several example contracts that represent different complexity levels:

- **assert_sum**: Simple spending validator with assertion
- **marketplace**: Complex contract with data structures  
- **gift**: Simple gift contract
- **dual_use**: Multi-purpose contract with special flags

## Optimization Levels

The tracker tests contracts with multiple optimization levels:
- **O1**: Basic optimizations
- **O2**: Standard optimizations (recommended)
- **O3**: Aggressive optimizations

## Usage

### For Developers

#### Check your changes locally:
```bash
python scripts/check_binary_sizes.py
```

This downloads the latest baseline and compares against your current code.

#### Manual comparison:
```bash
# Generate baseline from current code
python scripts/binary_size_tracker.py generate --baseline-file my_baseline.json

# Compare against baseline
python scripts/binary_size_tracker.py compare --baseline-file my_baseline.json
```

### For CI/CD

The binary size tracker runs automatically on pull requests. It:

1. Downloads the baseline from the latest release
2. Compiles contracts with current code
3. Compares sizes and reports changes
4. Comments on the PR with results
5. Fails the check if changes exceed the significant threshold (10%)

### For Releases

When a new release is created, the system automatically:

1. Generates a new baseline from the release code
2. Uploads the baseline as a release asset
3. Makes it available for future comparisons

## Configuration

Contract selection and thresholds are configurable via `scripts/binary_size_config.yaml`:

```yaml
contracts:
  - name: "contract_name"
    path: "path/to/contract.py"
    purpose: "spending"
    description: "Description of the contract"
    extra_flags: ["-fsome-flag"]  # optional

optimization_levels: ["O1", "O2", "O3"]

thresholds:
  warning: 5.0     # Warn if size changes by more than 5%
  significant: 10.0 # Mark as significant if size changes by more than 10%
```

## Output Format

The tracker reports changes in a clear format:

```
Contract: marketplace
Description: Marketplace contract with complex data structures
----------------------------------------
  O1: 8,876 → 9,200 bytes (+324 bytes, +3.6%)
  O2: 8,868 → 9,100 bytes (+232 bytes, +2.6%) ⚠️
  O3: 8,868 → 9,500 bytes (+632 bytes, +7.1%) ⚠️

Total size change across all contracts: +1,188 bytes
```

## Thresholds

- **< 5% change**: No warning
- **5-10% change**: Warning (⚠️)  
- **> 10% change**: Significant change (⚠️ SIGNIFICANT CHANGE)

## Files

- `scripts/binary_size_tracker.py`: Main tracking script
- `scripts/check_binary_sizes.py`: Convenience script for developers
- `scripts/binary_size_config.yaml`: Configuration file
- `.github/workflows/binary-size-tracker.yml`: CI workflow for PRs
- Binary baselines are stored as release assets

## Benefits

1. **Early Detection**: Catch size regressions before they reach production
2. **Optimization Tracking**: See how different optimization levels affect size
3. **Release Baseline**: Track size evolution across releases
4. **Cost Awareness**: Binary size directly impacts transaction fees
5. **Performance Monitoring**: Larger binaries may have execution implications