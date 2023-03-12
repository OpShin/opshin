#! /bin/bash
pip install pdoc3
pdoc --html eopsin -o docs
mv docs/html/* docs
