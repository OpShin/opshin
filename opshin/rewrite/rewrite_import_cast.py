import typing
from _ast import ImportFrom, AST, Call, Name
from typing import Optional
import pluthon as plt

from ..type_impls import (
    PolymorphicFunction,
    InstanceType,
    PolymorphicFunctionType,
    FunctionType,
    Type,
)
from ..type_inference import INITIAL_SCOPE
from ..util import CompilingNodeTransformer, OLambda, OVar
from ..typed_ast import *

"""
Injects the cast function if it is imported from typing

The cast function has special semantics:
- First argument is a type annotation (not evaluated as an expression)
- Second argument is the value to cast
- Returns the value with the target type
- At runtime, it's an identity function
"""

FunctionName = "cast"


class CastImpl(PolymorphicFunction):
    """
    Polymorphic function implementation for typing.cast().
    
    This receives the types of all arguments:
    - args[0]: target type (from first argument - type annotation)
    - args[1]: value type (from second argument - the value)
    
    Returns a function type where:
    - Input is the value type
    - Output is the target type
    """
    
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 2
        ), f"'cast' takes exactly 2 arguments (type and value), but {len(args)} were given"
        
        target_type = args[0]  # The type we're casting TO (a ClassType)
        value_type = args[1]   # The type of the value being cast (an InstanceType)
        
        # target_type is a ClassType (like IntegerType), value_type is an InstanceType
        assert isinstance(value_type, InstanceType), "Can only cast instance types"
        
        # Check type compatibility (X <= actual_type or actual_type <= X)
        # This is the same check as in AnnAssign (typed assignments)
        target_instance = InstanceType(target_type)
        assert (
            target_instance >= value_type or value_type >= target_instance
        ), f"Cannot cast between unrelated types: cannot cast {value_type.python_type()} to {target_instance.python_type()}"
        
        # Return a function type with both arguments, but returning the target type as InstanceType
        return FunctionType(args, target_instance)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        # cast is an identity function at runtime - just returns the value unchanged
        # The type checking is done at compile time
        return OLambda(["x"], OVar("x"))


class RewriteImportCast(CompilingNodeTransformer):
    step = "Resolving imports and usage of cast from typing"

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[AST]:
        if node.module != "typing":
            return node
        for n in node.names:
            if n.name == FunctionName:
                renamed = n.asname if n.asname is not None else n.name
                assert (
                    renamed not in INITIAL_SCOPE or renamed == FunctionName
                ), f"Name '{renamed}' is a reserved name, cannot import {FunctionName} with that name."
                INITIAL_SCOPE[renamed] = InstanceType(
                    PolymorphicFunctionType(CastImpl())
                )
        return node
