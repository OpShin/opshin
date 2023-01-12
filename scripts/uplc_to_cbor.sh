#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
aiken uplc flat /dev/stdin -p -c | python3 hex_to_bytes.py