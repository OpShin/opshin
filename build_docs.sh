#! /bin/bash
set -e

pip install pdoc3
rm -r docs/eopsin
pdoc --html eopsin -o docs
