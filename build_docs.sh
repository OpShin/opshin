#! /bin/bash
pip install handsdown
handsdown --external `git config --get remote.origin.url` -n eopsin --branch feat/docs --create-configs --exclude venv

