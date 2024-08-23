#! /bin/bash
set -e

rm -r docs/opshin || echo "docs/opshin was missing, that's ok"
poetry run pdoc --html opshin -o docs --template-dir docs
