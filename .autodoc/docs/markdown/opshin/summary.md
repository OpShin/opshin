[View code on GitHub](https://github.com/opshin/opshin/.autodoc/docs/json/opshin)

The `opshin` project provides a framework for compiling and evaluating Python programs into UPLC (Unspent Transaction Output Payable Contract) code, which is useful for developers who want to write smart contracts for the Cardano blockchain in Python. The project is organized into several modules and subfolders, each focusing on specific functionality, such as code compilation, optimization, type inference, and handling tokens at addresses.

For example, the `compiler.py` module is responsible for compiling a Python Abstract Syntax Tree (AST) into UPLC/Pluto-like code. It does so by implementing a series of transformations and optimizations on the input AST, ultimately producing a compiled program that can be executed in the UPLC/Pluto environment.

```python
from ast import parse
from opshin import compile

source_code = """
def validator(a: int, b: int) -> int:
    return a + b
"""

ast_tree = parse(source_code)
compiled_program = compile(ast_tree, force_three_params=False, validator_function_name="validator")
```

The `type_inference.py` module performs aggressive type inference on Python code, based on the work of Aycock [1]. The purpose of this type inference is to resolve overloaded functions when translating Python into UPLC, where there is no dynamic type checking. Additionally, it provides an extra layer of security for the Smart Contract by checking type correctness.

```python
from .type_inference import typed_ast
import ast

source_code = """
class MyClass:
    CONSTR_ID: int = 1
    attribute: int
"""

tree = ast.parse(source_code)
typed_tree = typed_ast(tree)
```

The `prelude.py` module defines a set of optimized methods for handling tokens at addresses in the opshin project. These functions are used to handle tokens at addresses in the opshin project, such as checking if a user has enough unlocked tokens to perform a transaction or validating the spending of a UTxO.

The `__main__.py` module provides a command-line interface for compiling and evaluating Python programs into UPLC code. This is useful for developers who want to write smart contracts for the Cardano blockchain in Python, which is a more familiar language for many developers than the low-level UPLC language.

```
$ python opshin.py eval my_contract.py 42 "hello world"
Starting execution
------------------
Hello, world! The answer is 42.
------------------
```

In summary, the `opshin` project offers a comprehensive solution for compiling and evaluating Python programs as UPLC code, making it easier for developers to write smart contracts for the Cardano blockchain. The project is organized into several modules and subfolders, each focusing on specific functionality, such as code compilation, optimization, type inference, and handling tokens at addresses.
