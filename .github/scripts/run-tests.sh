#!/bin/bash
set -ex

# Run pytest with coverage
uv run coverage run -m pytest tests

# Run opshin eval tests
uv run coverage run -a -m opshin eval examples/smart_contracts/assert_sum.py d8799fd8799f9fd8799fd8799f58205c25c47563872458e8607590c90c6ddadd0295f38c628426c4877185e721507a00ffd8799fd8799fd87a9f581c41582020bb0782bb76ce4fcd7ea2c2f3c565e1fd41a79ac7ddb3e145ffd87a80ffa140a1401a002dc6c0d87b9f14ffd87a80ffffff809fd8799fd8799fd8799f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffd87a80ffa140a1401a002ae91fd87980d87a80ffff1a0002dda1a080a0d8799fd8799fd87a9f1b00000199c356d9a8ffd87a80ffd8799fd87a9f1b00000199c3661be8ffd87980ffff9f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffa1d87a9fd8799f58205c25c47563872458e8607590c90c6ddadd0295f38c628426c4877185e721507a00ffff16a05820801ee2f936eb1dac69a6da43e17b09ade9bc8c3ed887066f350562d94c681573a080d87a80d87a80ff16d87a9fd8799f58205c25c47563872458e8607590c90c6ddadd0295f38c628426c4877185e721507a00ffd8799f14ffffff

# Compile tests
uv run coverage run -a -m opshin compile examples/smart_contracts/assert_sum.py > assert_sum.uplc

# More eval tests
uv run coverage run -a -m opshin eval_uplc examples/smart_contracts/assert_sum.py d8799fd8799f9fd8799fd8799f58205c25c47563872458e8607590c90c6ddadd0295f38c628426c4877185e721507a00ffd8799fd8799fd87a9f581c41582020bb0782bb76ce4fcd7ea2c2f3c565e1fd41a79ac7ddb3e145ffd87a80ffa140a1401a002dc6c0d87b9f14ffd87a80ffffff809fd8799fd8799fd8799f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffd87a80ffa140a1401a002ae91fd87980d87a80ffff1a0002dda1a080a0d8799fd8799fd87a9f1b00000199c356d9a8ffd87a80ffd8799fd87a9f1b00000199c3661be8ffd87980ffff9f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffa1d87a9fd8799f58205c25c47563872458e8607590c90c6ddadd0295f38c628426c4877185e721507a00ffff16a05820801ee2f936eb1dac69a6da43e17b09ade9bc8c3ed887066f350562d94c681573a080d87a80d87a80ff16d87a9fd8799f58205c25c47563872458e8607590c90c6ddadd0295f38c628426c4877185e721507a00ffd8799f14ffffff

# Pluto compile test
uv run coverage run -a -m opshin compile_pluto examples/smart_contracts/assert_sum.py

# Build tests
uv run coverage run -a -m opshin build examples/smart_contracts/assert_sum.py

# Compile all example files
for i in $(find examples/smart_contracts -type f -name "*.py" -not \( -name "broken*" -o -name "extract*" -o -name "wrapped_token*" -o -name "simple_script*" -o -name "parameterized*" \)); do
  uv run coverage run -a -m opshin compile "$i" --recursion-limit 4000 > /dev/null || exit
done
uv run coverage run -a -m opshin compile "examples/smart_contracts/wrapped_token.py" --recursion-limit 4000 --parameters 3 > /dev/null || exit
uv run coverage run -a -m opshin compile "examples/smart_contracts/simple_script.py" --recursion-limit 4000 --parameters 1 > /dev/null || exit
uv run coverage run -a -m opshin compile "examples/smart_contracts/parameterized.py" --recursion-limit 4000 --parameters 1 > /dev/null || exit

for i in $(find examples -type f -name "*.py" -not \( -name "broken*" -o -name "extract*" -o -name "wrapped_token*" -o -name "simple_script*" -o -name "parameterized*" \)); do
  uv run coverage run -a -m opshin compile "$i" --lib --recursion-limit 4000 -fno-unwrap-input -fno-wrap-output > /dev/null || exit
done

# Parameterized build test
uv run coverage run -a -m opshin build examples/smart_contracts/parameterized.py '{"int": 42}'

# Dual use tests with different optimization levels
uv run coverage run -a -m opshin build examples/smart_contracts/liquidity_pool.py
uv run coverage run -a -m opshin build examples/smart_contracts/liquidity_pool.py -O0
uv run coverage run -a -m opshin build examples/smart_contracts/liquidity_pool.py -O1
uv run coverage run -a -m opshin build examples/smart_contracts/liquidity_pool.py -O2
uv run coverage run -a -m opshin build examples/smart_contracts/liquidity_pool.py -O3

# Wrapped token test
uv run coverage run -a -m opshin build examples/smart_contracts/wrapped_token.py '{"bytes": "ae810731b5d21c0d182d89c60a1eff7095dffd1c0dce8707a8611099"}' '{"bytes": "4d494c4b"}' '{"int": 1000000}' --recursion-limit 4000

# Lint tests
test ! -n "$(uv run coverage run -a -m opshin lint examples/smart_contracts/always_true.py --recursion-limit 4000)"
test -n "$(uv run coverage run -a -m opshin lint examples/smart_contracts/wrapped_token.py --recursion-limit 4000)"
test -n "$(uv run coverage run -a -m opshin lint examples/broken.py --recursion-limit 4000)"
test -n "$(uv run coverage run -a -m opshin lint examples/broken.py --output-format-json --recursion-limit 4000)"

# Run linters (last so we see test failures first)
uv run black --check .

