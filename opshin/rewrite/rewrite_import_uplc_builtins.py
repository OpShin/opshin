import re
from copy import copy
from typing import Optional
from enum import Enum

from ..util import CompilingNodeTransformer
from ..typed_ast import *

"""
Checks that there was an import of wraps_builtin if there are any wrapped builtins
"""

DECORATOR_NAME = "wraps_builtin"


class RewriteImportUPLCBuiltins(CompilingNodeTransformer):
    step = "Resolving imports and usage of UPLC builtins"

    imports_uplc_builtins = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[AST]:
        if node.module != "opshin.bridge":
            return node
        for n in node.names:
            assert (
                n.name == DECORATOR_NAME
            ), "Imports something other from the bridge than the builtin wrapper"
            assert n.asname is None, "Renames the builtin wrapper. This is forbidden."
        self.imports_uplc_builtins = True
        return None

    def visit_FunctionDef(self, node: TypedFunctionDef) -> AST:
        if not node.decorator_list or len(node.decorator_list) != 1:
            return node
        is_wrapped = any(isinstance(n, Name) and n.id for n in node.decorator_list)
        if not is_wrapped:
            return node
        assert (
            self.imports_uplc_builtins
        ), "To wrap builtin functions, you need to import the builtin function. Add `from opshin.bridge import wraps_builtin` to your code."
        # we replace the body with a forwarded call to the wrapped builtin
        CamelCaseFunName = "".join(
            p.capitalize() for p in re.split(r"_(?!\d)", node.name)
        )
        uplc_fun = plt.__dict__[CamelCaseFunName]
        pluto_expression = RawPlutoExpr(
            typ=node.typ.typ.rettyp,
            expr=plt.Lambda(
                ["_"],
                uplc_fun(
                    *(plt.Var(f"p{i}") for i in range(len(node.args.args))),
                ),
            ),
        )
        node_cp = copy(node)
        node_cp.body = [Return(pluto_expression, typ=node.typ.typ.rettyp)]
        return node_cp
