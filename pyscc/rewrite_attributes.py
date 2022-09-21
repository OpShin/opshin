from typed_ast import *
from copy import copy

"""
Checks that there was an import of dataclass if there are any class definitions
"""

INITIAL_SCOPE = dict({
    "print": FunctionType([StringType], UnitType),
    "range": FunctionType(
        [IntegerType],
        TupleType([IntegerType, FunctionType([IntegerType], TupleType([BoolType, IntegerType, IntegerType]))])
    ),
    "int": FunctionType([PlutusDataType], IntegerType)
})


class RewriteAttributes(NodeTransformer):

    # A stack of dictionaries for storing scoped knowledge of variable types
    scopes = [INITIAL_SCOPE]

    # Obtain the type of a variable name in the current scope
    def variable_type(self, name: str):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def set_variable_type(self, name: str, typ: Type):
        self.scopes[-1][name] = typ

    def visit_Attribute(self, node: TypedAttribute) -> TypedSubscript:
        assert isinstance(node.value.typ, InstanceType), "Trying to access member of non-class-instance"
        cls = self.variable_type(node.value.typ.typ)
        assert isinstance(cls, ClassType)
        fieldindex = cls.record.attributes.index((node.attr, node.typ))
        # TODO
        return TypedSubscript(
            value=TypedCall(TypedName(id="__fields__")),
            slice=Index(value=TypedConstant(value=fieldindex, typ=InstanceType("int"))),
            typ=node.typ,
        )

