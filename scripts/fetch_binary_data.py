#!/usr/bin/env python3
"""
Fetch binary size data from GitHub releases and generate the documentation page from template.
This script runs during docs build to avoid CORS issues in the browser.
"""

import json
import subprocess
import sys
from pathlib import Path

import requests


def fetch_release_data():
    """Fetch all releases with binary size data from GitHub API."""
    print("Fetching releases from GitHub API...")

    try:
        response = requests.get("https://api.github.com/repos/OpShin/opshin/releases")
        response.raise_for_status()
        releases = response.json()

        releases_with_data = []

        for release in releases:
            # Look for binary_sizes_baseline.json in assets
            baseline_asset = None
            for asset in release.get("assets", []):
                if asset["name"] == "binary_sizes_baseline.json":
                    baseline_asset = asset
                    break

            if baseline_asset:
                try:
                    print(f"Downloading binary data for {release['tag_name']}...")
                    data_response = requests.get(baseline_asset["browser_download_url"])
                    data_response.raise_for_status()

                    binary_data = data_response.json()

                    releases_with_data.append(
                        {
                            "tag_name": release["tag_name"],
                            "name": release["name"],
                            "published_at": release["published_at"],
                            "html_url": release["html_url"],
                            "binary_data": binary_data,
                        }
                    )
                except Exception as e:
                    print(f"Failed to fetch binary data for {release['tag_name']}: {e}")

        print(f"Successfully fetched data for {len(releases_with_data)} releases")
        return releases_with_data

    except Exception as e:
        print(f"Error fetching releases: {e}")
        return []


def generate_html_from_template(releases_data, template_path, output_path):
    """Generate the final HTML file from template with embedded data."""

    # Read the template file
    with open(template_path) as f:
        template_content = f.read()

    # Create the JavaScript data embedding
    js_data = f"""<script>
const EMBEDDED_RELEASE_DATA = {json.dumps(releases_data, indent=2)};
</script>"""

    # Replace the placeholder with the embedded data
    html_content = template_content.replace(
        "<!-- EMBEDDED_DATA_PLACEHOLDER -->", js_data
    )

    # Write the final HTML file
    with open(output_path, "w") as f:
        f.write(html_content)

    print(
        f"Generated {output_path} from template with data for {len(releases_data)} releases"
    )
    return True


def fetch_current_dev_build_data():
    if not Path("binary_sizes_baseline.json").exists():
        subprocess.run("uv run scripts/binary_size_tracker.py generate", shell=True)
    else:
        print("Using existing binary_sizes_baseline.json file")
    current_dev_data_file = Path("binary_sizes_baseline.json")
    if current_dev_data_file.exists():
        try:
            with open(current_dev_data_file) as f:
                current_dev_data = json.load(f)
            return {
                "tag_name": "dev",
                "name": "Development Build",
                "published_at": "N/A",
                "html_url": "#",
                "binary_data": current_dev_data,
            }
            print("Added current development build data")
        except Exception as e:
            print(f"Failed to load current development build data: {e}")
    else:
        print("Current development build data file not found")


def main():
    """Main function to fetch data and generate HTML from template."""
    docs_dir = Path(__file__).parent.parent / "docs"
    template_file = docs_dir / "binary_size_trends.template.html"
    output_file = docs_dir / "binary_size_trends.html"

    if not template_file.exists():
        print(f"Template file not found: {template_file}")
        sys.exit(1)

    # Fetch release data
    releases_data = fetch_release_data()

    if not releases_data:
        print("No release data found, creating empty dataset")
        releases_data = []

    # Generate current dev build data
    current_dev_data = fetch_current_dev_build_data()
    if current_dev_data:
        releases_data.insert(0, current_dev_data)

    # Generate HTML file from template
    if generate_html_from_template(releases_data, template_file, output_file):
        print("Successfully generated HTML file from template with embedded data")
    else:
        print("Failed to generate HTML file from template")
        sys.exit(1)


if __name__ == "__main__":
    main()
