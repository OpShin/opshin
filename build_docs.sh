#! /bin/bash
set -e

pip install pdoc3
rm -r docs/eopsin || echo "docs/eopsin was missing, that's ok"
pdoc --html eopsin -o docs --template-dir docs
