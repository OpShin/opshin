#! /bin/bash
set -e

poetry run pip install pdoc3
poetry run pip install requests

# Generate binary size trends page from template with embedded data
echo "Generating binary size trends page from template..."
poetry run python scripts/fetch_binary_data.py

rm -r docs/opshin || echo "docs/opshin was missing, that's ok"
poetry run pdoc3 --html opshin -o docs --template-dir docs
