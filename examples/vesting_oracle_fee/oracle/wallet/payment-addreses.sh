#!/bin/bash


KEYS="oracle collateral"
CARDANO_NET="--testnet-magic 1"

for ADDR in $KEYS
do
  if [ -f "${ADDR}.skey" ] ; then
    echo "Key already exists!"
  else
    cardano-cli address key-gen --verification-key-file ${ADDR}.vkey --signing-key-file ${ADDR}.skey
    cardano-cli address build --payment-verification-key-file ${ADDR}.vkey --out-file ${ADDR}.addr ${CARDANO_NET}
    echo "${ADDR} address: $(cat ${ADDR}.addr)"
  fi
done
