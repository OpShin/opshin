#!/usr/bin/env python3
"""
Binary Size Tracker for OpShin

This script measures the binary sizes and execution costs of compiled OpShin contracts and can:
1. Generate a baseline measurement file for release artifacts
2. Compare current binary sizes and execution costs against a baseline (for PRs)
3. Report size and cost changes in a human-readable format

The script compiles a set of example contracts and measures their CBOR file sizes
and execution costs (CPU/MEM) across different optimization levels.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
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
        "4000",
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


def evaluate_contract(
    contract_path: str,
    purpose: str,
    optimization: str,
    test_inputs: Dict,
    extra_flags: Optional[List[str]] = None,
    work_dir: Optional[str] = None,
) -> Optional[Dict]:
    """
    Evaluate a contract with given inputs and return execution costs.
    Returns a dict with 'cpu' and 'memory' costs, or None if evaluation fails.
    
    test_inputs should have:
        - test_case_name: str
        - inputs_hex: List[str] - list of hex-encoded CBOR inputs
    """
    if work_dir is None:
        work_dir = os.getcwd()

    # Build command to evaluate the contract
    cmd = [
        "poetry",
        "run",
        "opshin",
        "eval_uplc",
        purpose,
        contract_path,
        f"-{optimization}",
        "--recursion-limit",
        "4000",
    ]

    if extra_flags:
        cmd.extend(extra_flags)

    # Add inputs as hex parameters
    for input_hex in test_inputs.get("inputs_hex", []):
        cmd.append(input_hex)

    exit_code, stdout, stderr = run_command(cmd, cwd=work_dir)

    if exit_code != 0:
        print(f"Failed to evaluate {contract_path}: {stderr}")
        return None

    # Parse the output to extract CPU and MEM costs
    # Expected format: "CPU: <number> | MEM: <number>"
    try:
        cost_line = None
        for line in stdout.splitlines():
            if "CPU:" in line and "MEM:" in line:
                cost_line = line
                break
        
        if cost_line is None:
            print(f"Could not find cost information in output")
            return None

        # Parse "CPU: 12345 | MEM: 67890"
        parts = cost_line.split("|")
        cpu_str = parts[0].split(":")[1].strip()
        mem_str = parts[1].split(":")[1].strip()
        
        return {
            "cpu": int(cpu_str),
            "memory": int(mem_str)
        }
    except Exception as e:
        print(f"Failed to parse execution costs: {e}")
        print(f"Output was: {stdout}")
        return None


def measure_contract_sizes(
    contracts: List[Dict],
    optimization_levels: List[str],
    work_dir: Optional[str] = None,
) -> Dict:
    """
    Measure binary sizes and execution costs for all contracts and optimization levels.
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
        test_inputs_list = contract.get("test_inputs", [])

        print(f"Measuring {name}...")

        contract_results = {}
        for opt_level in optimization_levels:
            size = compile_contract(path, purpose, opt_level, extra_flags, work_dir)
            if size is not None:
                contract_results[opt_level] = {"size": size}
                print(f"  {opt_level}: {size} bytes")
                
                # Measure execution costs if test inputs are provided
                if test_inputs_list:
                    execution_costs = []
                    for test_inputs in test_inputs_list:
                        test_case_name = test_inputs.get("test_case_name", "unnamed")
                        print(f"    Evaluating test case: {test_case_name}")
                        costs = evaluate_contract(
                            path, purpose, opt_level, test_inputs, extra_flags, work_dir
                        )
                        if costs:
                            execution_costs.append({
                                "test_case": test_case_name,
                                "cpu": costs["cpu"],
                                "memory": costs["memory"]
                            })
                            print(f"      CPU: {costs['cpu']:,} | MEM: {costs['memory']:,}")
                        else:
                            execution_costs.append({
                                "test_case": test_case_name,
                                "cpu": None,
                                "memory": None
                            })
                            print(f"      FAILED to evaluate")
                    
                    contract_results[opt_level]["execution_costs"] = execution_costs
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
    """Generate baseline measurements (sizes and execution costs) and save to file"""
    print("Generating baseline binary size and execution cost measurements...")

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
    Compare current measurements (sizes and execution costs) with baseline.
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

    print("Measuring current binary sizes and execution costs...")
    current = measure_contract_sizes(
        config["contracts"], config["optimization_levels"], work_dir
    )

    print("\n" + "=" * 60)
    print("BINARY SIZE AND EXECUTION COST COMPARISON REPORT")
    print("=" * 60)

    has_changes = False
    total_size_change = 0

    for contract_config in config["contracts"]:
        name = contract_config["name"]
        if name not in baseline["contracts"] or name not in current["contracts"]:
            print(f"\nContract {name}: MISSING in baseline or current")
            continue

        def print_contract_info():
            print(f"\nContract: {name}")
            print(f"Description: {current['contracts'][name]['description']}")
            print("-" * 40)

        baseline_contract = baseline["contracts"][name]
        current_contract = current["contracts"][name]

        any_increase = False
        prev_opt_level_size = float("inf")
        for opt_level in config["optimization_levels"]:
            baseline_data = baseline_contract["sizes"].get(opt_level)
            current_data = current_contract["sizes"].get(opt_level)
            ignore_warnings = opt_level in config.get("ignore_warnings", [])

            # Handle both old format (int) and new format (dict with 'size' key)
            baseline_size = baseline_data if isinstance(baseline_data, int) else (baseline_data.get("size") if baseline_data else None)
            current_size = current_data if isinstance(current_data, int) else (current_data.get("size") if current_data else None)

            if current_size is not None:
                size_diff = current_size - prev_opt_level_size
                size_percent = (
                    (size_diff / prev_opt_level_size) * 100
                    if prev_opt_level_size > 0 and prev_opt_level_size != float("inf")
                    else 0
                )
                status = ""
                increased = size_diff > 0
                if size_percent > significant_threshold:
                    has_changes = True if not ignore_warnings else has_changes
                    status = " ⚠️  SIGNIFICANT CHANGE" + (
                        " (ignored)" if ignore_warnings else ""
                    )
                elif size_percent > warning_threshold:
                    has_changes = True if not ignore_warnings else has_changes
                    status = " ⚠️" + (" (ignored)" if ignore_warnings else "")
                if increased and prev_opt_level_size != float("inf"):
                    if not any_increase:
                        print_contract_info()
                    any_increase = True
                    print(
                        f"  {opt_level}: {prev_opt_level_size:,} → {current_size:,} bytes (increased from previous level by {size_diff:+,} bytes, {size_percent:+.1f}%) {status}"
                    )
            prev_opt_level_size = current_size if current_size is not None else prev_opt_level_size

            if baseline_size is None or current_size is None:
                if not any_increase:
                    print_contract_info()
                any_increase = True
                print(f"  {opt_level}: MISSING DATA")
                continue

            status = ""
            size_diff = current_size - baseline_size
            size_percent = (size_diff / baseline_size) * 100 if baseline_size > 0 else 0
            changed = size_diff != 0

            if size_percent > significant_threshold:
                has_changes = True if not ignore_warnings else has_changes
                status = " ⚠️  SIGNIFICANT CHANGE" + (
                    " (ignored)" if ignore_warnings else ""
                )
            elif size_percent > warning_threshold:
                has_changes = True if not ignore_warnings else has_changes
                status = " ⚠️" + (" (ignored)" if ignore_warnings else "")
            elif size_percent < 0:
                status = " ↘️ (size reduced)"

            if changed:
                if not any_increase:
                    print_contract_info()
                any_increase = True
                print(
                    f"  {opt_level}: {baseline_size:,} → {current_size:,} bytes "
                    f"({size_diff:+,} bytes, {size_percent:+.1f}%){status}"
                )

            total_size_change += size_diff

            # Compare execution costs if available
            if isinstance(current_data, dict) and "execution_costs" in current_data:
                baseline_costs = baseline_data.get("execution_costs", []) if isinstance(baseline_data, dict) else []
                current_costs = current_data.get("execution_costs", [])
                
                # Compare costs for each test case
                for current_cost in current_costs:
                    test_case = current_cost.get("test_case")
                    current_cpu = current_cost.get("cpu")
                    current_mem = current_cost.get("memory")
                    
                    if current_cpu is None or current_mem is None:
                        continue
                    
                    # Find matching baseline test case
                    baseline_cost = next(
                        (bc for bc in baseline_costs if bc.get("test_case") == test_case),
                        None
                    )
                    
                    if baseline_cost and baseline_cost.get("cpu") is not None:
                        baseline_cpu = baseline_cost.get("cpu")
                        baseline_mem = baseline_cost.get("memory")
                        
                        cpu_diff = current_cpu - baseline_cpu
                        mem_diff = current_mem - baseline_mem
                        cpu_percent = (cpu_diff / baseline_cpu) * 100 if baseline_cpu > 0 else 0
                        mem_percent = (mem_diff / baseline_mem) * 100 if baseline_mem > 0 else 0
                        
                        cost_status = ""
                        if cpu_percent > significant_threshold or mem_percent > significant_threshold:
                            has_changes = True if not ignore_warnings else has_changes
                            cost_status = " ⚠️  SIGNIFICANT CHANGE" + (
                                " (ignored)" if ignore_warnings else ""
                            )
                        elif cpu_percent > warning_threshold or mem_percent > warning_threshold:
                            has_changes = True if not ignore_warnings else has_changes
                            cost_status = " ⚠️" + (" (ignored)" if ignore_warnings else "")
                        elif cpu_percent < 0 and mem_percent < 0:
                            cost_status = " ↘️ (costs reduced)"
                        
                        if cpu_diff != 0 or mem_diff != 0:
                            print(
                                f"    Test '{test_case}': CPU {baseline_cpu:,} → {current_cpu:,} "
                                f"({cpu_diff:+,}, {cpu_percent:+.1f}%) | "
                                f"MEM {baseline_mem:,} → {current_mem:,} "
                                f"({mem_diff:+,}, {mem_percent:+.1f}%){cost_status}"
                            )
                    else:
                        # New test case with no baseline
                        print(
                            f"    Test '{test_case}' (new): CPU {current_cpu:,} | MEM {current_mem:,}"
                        )

    print(
        f"\nTotal size change compared to previous release: {total_size_change:+,} bytes"
    )

    if has_changes:
        print("\n⚠️  SIGNIFICANT CHANGES DETECTED")
        print(
            "Please review the changes and consider optimization if sizes or costs increased significantly."
        )
    else:
        print("\n✅ No significant changes detected")

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
