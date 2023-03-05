#! /bin/bash
pip install handsdown
handsdown --external `git config --get remote.origin.url` -n eopsin --branch master --create-configs --exclude venv

