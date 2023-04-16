[View code on GitHub](https://github.com/opshin/opshin/.autodoc/docs/json/opshin/rewrite)

The code in the `.autodoc/docs/json/opshin/rewrite` folder is responsible for various transformations and checks on Python code, primarily focusing on ensuring proper usage of imports, type annotations, and assignments. These transformations and checks are implemented using classes that inherit from the `CompilingNodeTransformer` class, which provides a framework for modifying and transforming Python abstract syntax trees (ASTs).

For example, the `RewriteAugAssign` class rewrites all occurrences of augmented assignments into normal assignments, simplifying the logic of the code that operates on these assignments. The `RewriteForbiddenOverwrites` class prevents certain variable names from being overwritten, which is useful in projects that make use of type annotations or custom decorators.

The `RewriteImportDataclasses` and `RewriteImportTyping` classes ensure that the `dataclasses` and `typing` modules are imported and used correctly in a Python program, which is important for maintaining code quality and consistency. The `RewriteInjectBuiltinsConstr` class injects constructors for built-in types that double function as type annotations, ensuring that classes are not reassigned without a constructor.

Here's an example of how the `RewriteAugAssign` class can be used:

```python
from ast import parse
from opshin.rewrite_aug_assign import RewriteAugAssign

code = "x += 1"
tree = parse(code)
rewriter = RewriteAugAssign()
new_tree = rewriter.visit(tree)
print(new_tree)
```

Output:
```
Module(body=[Assign(targets=[Name(id='x', ctx=Store())], value=BinOp(left=Name(id='x', ctx=Load()), op=Add(), right=Constant(value=1)))])
```

In summary, the code in the `.autodoc/docs/json/opshin/rewrite` folder provides a set of tools for transforming and checking Python code to ensure proper usage of imports, type annotations, and assignments. These tools can be used as part of a larger code analysis or linting tool to enforce best practices and maintain code quality and consistency.
