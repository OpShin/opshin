#!/usr/bin/env python3
"""
OpShin Binary Size Check Tool

A convenience script for developers to check binary sizes locally.
This downloads the latest baseline and compares against current code.
"""

import argparse
import os
import requests
import sys
import tempfile
from pathlib import Path


def download_latest_baseline(repo: str = "OpShin/opshin") -> str:
    """Download the latest baseline from GitHub releases"""
    print("Downloading latest binary size baseline from GitHub...")

    # Get latest release info
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        release_data = response.json()
    except Exception as e:
        print(f"Failed to fetch release info: {e}")
        return None

    # Find baseline asset
    baseline_asset = None
    for asset in release_data.get("assets", []):
        if asset["name"] == "binary_sizes_baseline.json":
            baseline_asset = asset
            break

    if not baseline_asset:
        print("No binary size baseline found in latest release")
        return None

    # Download baseline
    try:
        baseline_response = requests.get(baseline_asset["browser_download_url"])
        baseline_response.raise_for_status()

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        temp_file.write(baseline_response.text)
        temp_file.close()

        print(f"Downloaded baseline from release {release_data['tag_name']}")
        return temp_file.name

    except Exception as e:
        print(f"Failed to download baseline: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Check binary sizes against latest release baseline"
    )
    parser.add_argument(
        "--repo",
        default="OpShin/opshin",
        help="GitHub repository (default: OpShin/opshin)",
    )
    parser.add_argument(
        "--baseline-file", help="Use local baseline file instead of downloading"
    )

    args = parser.parse_args()

    # Find the binary size tracker script
    script_dir = Path(__file__).parent
    tracker_script = script_dir / "binary_size_tracker.py"

    if not tracker_script.exists():
        print(f"Error: {tracker_script} not found")
        sys.exit(1)

    # Get baseline file
    if args.baseline_file:
        baseline_file = args.baseline_file
        if not os.path.exists(baseline_file):
            print(f"Error: Baseline file {baseline_file} not found")
            sys.exit(1)
    else:
        baseline_file = download_latest_baseline(args.repo)
        if not baseline_file:
            print("Failed to get baseline file")
            sys.exit(1)

    try:
        # Run the comparison
        print("\nRunning binary size comparison...")
        os.system(f"python {tracker_script} compare --baseline-file {baseline_file}")

    finally:
        # Clean up temp file if we downloaded it
        if not args.baseline_file and baseline_file and os.path.exists(baseline_file):
            os.unlink(baseline_file)


if __name__ == "__main__":
    main()
