#!/bin/bash
set -e

# Run linters
poetry run black --check .

# Run pytest with coverage
poetry run coverage run -m pytest tests

# Run opshin eval tests
poetry run coverage run -a -m opshin eval spending examples/smart_contracts/assert_sum.py "{\"int\": 4}" "{\"int\": 38}" d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87980d87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820746957f0eb57f2b11119684e611a98f373afea93473fefbb7632d579af2f6259ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff

# Compile tests
poetry run coverage run -a -m opshin compile spending examples/smart_contracts/assert_sum.py > assert_sum.uplc

# More eval tests
poetry run coverage run -a -m opshin eval_uplc spending examples/smart_contracts/assert_sum.py "{\"int\": 4}" "{\"int\": 38}" d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87980d87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820746957f0eb57f2b11119684e611a98f373afea93473fefbb7632d579af2f6259ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff

# Pluto compile test
poetry run coverage run -a -m opshin compile_pluto spending examples/smart_contracts/assert_sum.py

# Build tests
poetry run coverage run -a -m opshin build spending examples/smart_contracts/assert_sum.py

# Compile all example files
for i in $(find examples -type f -name "*.py" -not \( -name "broken*" -o -name "extract*" \)); do
  echo "$i"
  poetry run coverage run -a -m opshin compile any "$i" > /dev/null || exit
done

# Parameterized build test
poetry run coverage run -a -m opshin build spending examples/smart_contracts/parameterized.py '{"int": 42}'

# Dual use tests with different optimization levels
poetry run coverage run -a -m opshin build spending examples/smart_contracts/dual_use.py -fforce-three-params
poetry run coverage run -a -m opshin build spending examples/smart_contracts/dual_use.py -fforce-three-params -O0
poetry run coverage run -a -m opshin build spending examples/smart_contracts/dual_use.py -fforce-three-params -O1
poetry run coverage run -a -m opshin build spending examples/smart_contracts/dual_use.py -fforce-three-params -O2
poetry run coverage run -a -m opshin build spending examples/smart_contracts/dual_use.py -fforce-three-params -O3

# Wrapped token test
poetry run coverage run -a -m opshin build spending examples/smart_contracts/wrapped_token.py '{"bytes": "ae810731b5d21c0d182d89c60a1eff7095dffd1c0dce8707a8611099"}' '{"bytes": "4d494c4b"}' '{"int": 1000000}' -fforce-three-params

# Lint tests
test ! -n "$(poetry run coverage run -a -m opshin lint any examples/smart_contracts/always_true.py)"
test -n "$(poetry run coverage run -a -m opshin lint any examples/smart_contracts/wrapped_token.py)"
test -n "$(poetry run coverage run -a -m opshin lint any examples/broken.py)"
test -n "$(poetry run coverage run -a -m opshin lint any examples/broken.py --output-format-json)"

# Prelude compile test
poetry run coverage run -a -m opshin compile lib opshin/prelude.py -fno-remove-dead-code

# Compile all std and ledger files
for i in $(find opshin/std opshin/ledger -type f -name "*.py" ! -name "*integrity.py"); do
  echo "$i"
  poetry run coverage run -a -m opshin compile lib "$i" -fno-remove-dead-code > /dev/null || exit
done