#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m eopsin compile /dev/stdin | bash uplc_to_flat.sh | python3 flat_to_cbor.py | python3 cbor_to_plutus.py