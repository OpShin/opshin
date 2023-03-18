#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m opshin compile_pluto /dev/stdin | bash pluto_to_cbor.sh | python3 cbor_to_plutus.py