#!/usr/bin/env python3
"""
Binary Size Tracker for OpShin

This script measures the binary sizes of compiled OpShin contracts and can:
1. Generate a baseline measurement file for release artifacts
2. Compare current binary sizes against a baseline (for PRs)
3. Report size changes in a human-readable format

The script compiles a set of example contracts and measures their CBOR file sizes
across different optimization levels.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_config(config_file: Optional[str] = None) -> Dict:
    """Load configuration from YAML file"""
    if config_file is None:
        config_file = Path(__file__).parent / "binary_size_config.yaml"

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Failed to load config from {config_file}: {e}")
        # Fallback to default configuration
        return {
            "contracts": [
                {
                    "name": "assert_sum",
                    "path": "examples/smart_contracts/assert_sum.py",
                    "purpose": "spending",
                    "description": "Simple spending validator with assertion",
                },
                {
                    "name": "marketplace",
                    "path": "examples/smart_contracts/marketplace.py",
                    "purpose": "spending",
                    "description": "Marketplace contract with complex data structures",
                },
                {
                    "name": "gift",
                    "path": "examples/smart_contracts/gift.py",
                    "purpose": "spending",
                    "description": "Gift contract with simple logic",
                },
                {
                    "name": "dual_use",
                    "path": "examples/smart_contracts/dual_use.py",
                    "purpose": "spending",
                    "extra_flags": ["-fforce-three-params"],
                    "description": "Dual-use contract with multiple entry points",
                },
            ],
            "optimization_levels": ["O1", "O2", "O3"],
            "thresholds": {"warning": 5.0, "significant": 10.0},
        }


def run_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def compile_contract(
    contract_path: str,
    purpose: str,
    optimization: str,
    extra_flags: Optional[List[str]] = None,
    work_dir: Optional[str] = None,
) -> Optional[int]:
    """
    Compile a contract and return the CBOR file size in bytes.
    Returns None if compilation fails.
    """
    if work_dir is None:
        work_dir = os.getcwd()

    output_dir = f"size_test_{optimization}"

    cmd = [
        "poetry",
        "run",
        "opshin",
        "build",
        purpose,
        contract_path,
        f"-{optimization}",
        "--recursion-limit",
        "2000",
        "-o",
        output_dir,
    ]

    if extra_flags:
        cmd.extend(extra_flags)

    exit_code, stdout, stderr = run_command(cmd, cwd=work_dir)

    if exit_code != 0:
        print(f"Failed to compile {contract_path} with {optimization}: {stderr}")
        return None

    cbor_file = Path(work_dir) / output_dir / "script.cbor"
    if cbor_file.exists():
        size = cbor_file.stat().st_size
        # Clean up
        shutil.rmtree(Path(work_dir) / output_dir, ignore_errors=True)
        return size
    else:
        print(f"CBOR file not found for {contract_path}")
        return None


def measure_contract_sizes(
    contracts: List[Dict],
    optimization_levels: List[str],
    work_dir: Optional[str] = None,
) -> Dict:
    """
    Measure binary sizes for all contracts and optimization levels.
    Returns a dict with the measurements.
    """
    results = {
        "contracts": {},
        "metadata": {
            "optimization_levels": optimization_levels,
            "total_contracts": len(contracts),
        },
    }

    for contract in contracts:
        name = contract["name"]
        path = contract["path"]
        purpose = contract["purpose"]
        extra_flags = contract.get("extra_flags", [])

        print(f"Measuring {name}...")

        contract_results = {}
        for opt_level in optimization_levels:
            size = compile_contract(path, purpose, opt_level, extra_flags, work_dir)
            if size is not None:
                contract_results[opt_level] = size
                print(f"  {opt_level}: {size} bytes")
            else:
                print(f"  {opt_level}: FAILED")
                contract_results[opt_level] = None

        results["contracts"][name] = {
            "sizes": contract_results,
            "path": path,
            "purpose": purpose,
            "description": contract.get("description", ""),
            "extra_flags": extra_flags,
        }

    return results


def generate_baseline(
    output_file: str, work_dir: Optional[str] = None, config_file: Optional[str] = None
) -> None:
    """Generate baseline measurements and save to file"""
    print("Generating baseline binary size measurements...")

    config = load_config(config_file)
    results = measure_contract_sizes(
        config["contracts"], config["optimization_levels"], work_dir
    )

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Baseline saved to {output_file}")


def compare_with_baseline(
    baseline_file: str,
    work_dir: Optional[str] = None,
    config_file: Optional[str] = None,
) -> bool:
    """
    Compare current measurements with baseline.
    Returns True if there are significant changes, False otherwise.
    """
    if not os.path.exists(baseline_file):
        print(f"Baseline file {baseline_file} not found")
        return False

    config = load_config(config_file)
    warning_threshold = config["thresholds"]["warning"]
    significant_threshold = config["thresholds"]["significant"]

    print("Loading baseline measurements...")
    with open(baseline_file, "r") as f:
        baseline = json.load(f)

    print("Measuring current binary sizes...")
    current = measure_contract_sizes(
        config["contracts"], config["optimization_levels"], work_dir
    )

    print("\n" + "=" * 60)
    print("BINARY SIZE COMPARISON REPORT")
    print("=" * 60)

    has_changes = False
    total_size_change = 0

    for contract_config in config["contracts"]:
        name = contract_config["name"]
        if name not in baseline["contracts"] or name not in current["contracts"]:
            print(f"\nContract {name}: MISSING in baseline or current")
            continue

        print(f"\nContract: {name}")
        print(f"Description: {current['contracts'][name]['description']}")
        print("-" * 40)

        baseline_contract = baseline["contracts"][name]
        current_contract = current["contracts"][name]

        prev_opt_level_size = float("inf")
        for opt_level in config["optimization_levels"]:
            baseline_size = baseline_contract["sizes"].get(opt_level)
            current_size = current_contract["sizes"].get(opt_level)
            ignore_warnings = opt_level in config["ignore_warnings"]

            if current_size is not None and current_size > prev_opt_level_size:
                has_changes = True
                size_diff = current_size - prev_opt_level_size
                size_percent = (
                    (size_diff / prev_opt_level_size) * 100
                    if prev_opt_level_size > 0
                    else 0
                )
                print(
                    f"  {opt_level}: {current_size:,} bytes (increased from previous level by {size_diff:+,} bytes, {size_percent:+.1f}%) {status}"
                )
            prev_opt_level_size = current_size

            if baseline_size is None or current_size is None:
                print(f"  {opt_level}: MISSING DATA")
                continue

            status = ""
            size_diff = current_size - baseline_size
            size_percent = (size_diff / baseline_size) * 100 if baseline_size > 0 else 0

            if size_percent > significant_threshold:
                has_changes = True if not ignore_warnings else has_changes
                status = " ⚠️  SIGNIFICANT CHANGE" + (
                    " (ignored)" if ignore_warnings else ""
                )
            elif size_percent > warning_threshold:
                has_changes = True if not ignore_warnings else has_changes
                status = " ⚠️" + (" (ignored)" if ignore_warnings else "")

            print(
                f"  {opt_level}: {baseline_size:,} → {current_size:,} bytes "
                f"({size_diff:+,} bytes, {size_percent:+.1f}%){status}"
            )

            total_size_change += size_diff

    print(f"\nTotal size change across all contracts: {total_size_change:+,} bytes")

    if has_changes:
        print("\n⚠️  SIGNIFICANT BINARY SIZE CHANGES DETECTED")
        print(
            "Please review the changes and consider optimization if sizes increased significantly."
        )
    else:
        print("\n✅ No significant binary size changes detected")

    print("=" * 60)

    return has_changes


def main():
    parser = argparse.ArgumentParser(
        description="Binary Size Tracker for OpShin contracts"
    )
    parser.add_argument(
        "action",
        choices=["generate", "compare"],
        help="Action to perform: generate baseline or compare with baseline",
    )
    parser.add_argument(
        "--baseline-file",
        default="binary_sizes_baseline.json",
        help="Path to baseline file (default: binary_sizes_baseline.json)",
    )
    parser.add_argument(
        "--work-dir", help="Working directory (defaults to current directory)"
    )
    parser.add_argument(
        "--config-file", help="Configuration file (defaults to binary_size_config.yaml)"
    )

    args = parser.parse_args()

    if args.action == "generate":
        generate_baseline(args.baseline_file, args.work_dir, args.config_file)
    elif args.action == "compare":
        has_changes = compare_with_baseline(
            args.baseline_file, args.work_dir, args.config_file
        )
        # Exit with code 1 if there are significant changes (for CI)
        sys.exit(1 if has_changes else 0)


if __name__ == "__main__":
    main()
