[View code on GitHub](https://github.com/opshin/opshin/.autodoc/docs/json/scripts)

The `.autodoc/docs/json/scripts` folder contains various scripts that are used for converting and compiling data in different formats within the opshin project. These scripts are primarily written in Python and Bash and are designed to work together to achieve specific tasks related to data conversion and compilation.

For instance, the `cbor_to_plutus.py` script is responsible for converting input data into a JSON object that can be used as a Smart Contract in the opshin project. It reads input data from standard input, encodes it into CBOR format, and then converts it to a hexadecimal string. The resulting JSON object can be used in other parts of the project to execute the Smart Contract. Example usage:

```bash
$ echo "hello world" | python contract_builder.py
{"type": "PlutusScriptV2", "description": "opshin 1.0.0 Smart Contract", "cborHex": "430a68656c6c6f20776f726c64"}
```

The `hex_to_bytes.py` script is a simple utility that converts a hexadecimal string to bytes and outputs the result. This functionality may be useful in various parts of the larger project, such as when dealing with binary data or network protocols that use hexadecimal encoding.

The `pluto_to_cbor.sh` script is a Bash script that uses the pluto tool to assemble input data and output the result to standard output. This script provides a convenient way to use the pluto tool within the larger opshin project, allowing developers to easily generate code in multiple programming languages from a single source file.

The `python_to_plutus_via_aiken.sh` script compiles a program written in the Opshin language into a format that can be executed on the Plutus platform. This script allows developers to write their smart contracts in a high-level language that is easier to work with than Plutus Core, while still being able to take advantage of the features provided by the Plutus platform.

The `python_to_plutus_via_pluto.sh` script compiles a program written in the Pluto programming language into CBOR format and then converts it back into Pluto format. This script is likely used as part of a larger project that involves compiling and executing Pluto programs.

Lastly, the `uplc_to_cbor.sh` script is a Bash script that takes in a hexadecimal string as input and converts it to bytes using a Python script. This functionality could be useful in various parts of the opshin project that require working with binary data, such as cryptography or network protocols.

Overall, the scripts in this folder provide essential functionality for data conversion and compilation within the opshin project. They are designed to work together and can be used in various parts of the project to achieve specific tasks related to data manipulation and processing.
