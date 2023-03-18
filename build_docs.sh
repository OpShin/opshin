#! /bin/bash
set -e

pip install pdoc3
rm -r docs/opshin || echo "docs/opshin was missing, that's ok"
pdoc --html opshin -o docs --template-dir docs
