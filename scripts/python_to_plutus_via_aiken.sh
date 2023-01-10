#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m eopsin compile /dev/stdin | bash uplc_to_cbor.sh | python3 hex_to_bytes.py | python3 cbor_to_plutus.py