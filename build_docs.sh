#! /bin/bash
set -e

poetry run pip install pdoc3
rm -r docs/opshin || echo "docs/opshin was missing, that's ok"
poetry run pdoc3 --html opshin -o docs --template-dir docs
