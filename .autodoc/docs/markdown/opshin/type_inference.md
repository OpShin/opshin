[View code on GitHub](https://github.com/opshin/opshin/opshin/type_inference.py)

The code in this file is responsible for performing aggressive type inference on Python code, based on the work of Aycock [1]. The purpose of this type inference is to resolve overloaded functions when translating Python into UPLC, where there is no dynamic type checking. Additionally, it provides an extra layer of security for the Smart Contract by checking type correctness.

The `AggressiveTypeInferencer` class is a subclass of `CompilingNodeTransformer` and is responsible for performing type inference on the given AST. It maintains a stack of dictionaries called `scopes` to store variable types in different scopes. The class provides methods to enter and exit scopes, set variable types, and infer types from annotations.

The `visit_*` methods are implemented for various AST nodes, such as `visit_ClassDef`, `visit_FunctionDef`, `visit_Module`, and others. These methods perform type inference on the respective nodes and return typed versions of the nodes (e.g., `TypedClassDef`, `TypedFunctionDef`, etc.).

The `RecordReader` class is a subclass of `NodeVisitor` and is responsible for extracting information about a class definition, such as its name, constructor, and attributes. It uses the `AggressiveTypeInferencer` to infer types for the attributes.

The `typed_ast` function takes an AST as input and returns a typed version of the AST by using the `AggressiveTypeInferencer`.

Example usage:

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

In this example, the `typed_ast` function is used to perform type inference on the given source code and return a typed version of the AST.

[1]: https://legacy.python.org/workshops/2000-01/proceedings/papers/aycock/aycock.html
## Questions: 
 1. **Question**: What is the purpose of the `AggressiveTypeInferencer` class?
   **Answer**: The `AggressiveTypeInferencer` class is a type inference system based on the work of Aycock. It is designed to statically infer the type of all involved variables in a subset of legal Python operations, which helps in resolving overloaded functions when translating Python into UPLC where there is no dynamic type checking. It also adds an additional layer of security to the Smart Contract by checking type correctness.

2. **Question**: How does the `type_from_annotation` method work?
   **Answer**: The `type_from_annotation` method takes an annotation expression as input and returns the corresponding type. It supports various types of annotations, such as `Constant`, `Name`, `Subscript`, and `None`. It handles different cases for each type of annotation and raises a `NotImplementedError` if an unsupported annotation type is encountered.

3. **Question**: How does the `visit_FunctionDef` method handle function definitions?
   **Answer**: The `visit_FunctionDef` method processes a function definition by first entering a new scope, visiting the function arguments, and inferring the function type based on the argument types and return type annotation. It then sets the function type in the current scope for potential recursion. After that, it visits the function body, checks if the return type matches the annotated return type, and exits the scope. Finally, it sets the function type outside the scope for usage and returns the typed function definition.