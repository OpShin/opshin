import typing
import ast
from collections import defaultdict
import builtins
from contextlib import contextmanager
import dataclasses
import importlib
import logging
import sys
import types

from ast import *
from ordered_set import OrderedSet

from pycardano import PlutusData

try:
    unparse
except NameError:
    from astunparse import unparse

from ..util import CompilingNodeTransformer, CompilingNodeVisitor, OPSHIN_LOGGER
from ..type_inference import INITIAL_SCOPE

"""
Pre-evaluates constant statements
"""

ACCEPTED_ATOMIC_TYPES = [
    int,
    str,
    bytes,
    type(None),
    bool,
]

SAFE_GLOBALS_LIST = [
    abs,
    all,
    any,
    ascii,
    bin,
    bool,
    bytes,
    bytearray,
    callable,
    chr,
    complex,
    dict,
    divmod,
    enumerate,
    filter,
    float,
    format,
    frozenset,
    hex,
    int,
    isinstance,
    issubclass,
    iter,
    len,
    list,
    map,
    max,
    min,
    next,
    oct,
    ord,
    pow,
    range,
    repr,
    reversed,
    round,
    set,
    slice,
    sorted,
    str,
    sum,
    tuple,
    zip,
]
SAFE_GLOBALS = {x.__name__: x for x in SAFE_GLOBALS_LIST}

TRUSTED_IMPORTS = {
    "pycardano": {"Datum", "PlutusData"},
    "typing": {"Dict", "List", "Optional", "Self", "Tuple", "Union"},
    "dataclasses": {"astuple", "dataclass"},
    "hashlib": {"blake2b", "sha256", "sha3_256"},
    "opshin.bridge": {"wraps_builtin"},
    "opshin.std.integrity": {"check_integrity"},
    "opshin.std.bls12_381": {
        "BLS12381G1Element",
        "BLS12381G2Element",
        "BLS12381MillerLoopResult",
    },
}


class UnsafeConstantExpression(ValueError):
    pass


class ConstantEvaluationLimitExceeded(UnsafeConstantExpression):
    pass


@contextmanager
def _constant_evaluation_budget(max_steps: int = 100_000):
    """Bound Python work performed while evaluating an optimization candidate."""
    previous_trace = sys.gettrace()
    steps = 0

    def count_steps(frame, event, arg):
        nonlocal steps
        if event == "call":
            frame.f_trace_opcodes = True
        if event in ("call", "line", "opcode"):
            steps += 1
            if steps > max_steps:
                raise ConstantEvaluationLimitExceeded(
                    "Compile-time constant evaluation exceeded its execution budget"
                )
        return count_steps

    sys.settrace(count_steps)
    try:
        yield
    finally:
        sys.settrace(previous_trace)


def _matches_annotation(value, annotation) -> bool:
    """Check the runtime shape that an Opshin datum annotation promises."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if annotation is typing.Any:
        return True
    if origin in (typing.Union, types.UnionType):
        return any(_matches_annotation(value, option) for option in args)
    if origin is list:
        return type(value) is list and all(
            _matches_annotation(element, args[0]) for element in value
        )
    if origin is dict:
        return type(value) is dict and all(
            _matches_annotation(key, args[0]) and _matches_annotation(element, args[1])
            for key, element in value.items()
        )
    if annotation in (int, bytes, bool, str, type(None)):
        return type(value) is annotation
    if isinstance(annotation, type) and issubclass(annotation, PlutusData):
        if annotation is not PlutusData and type(value) is not annotation:
            return False
        if not isinstance(value, PlutusData):
            return False
        return all(
            _matches_annotation(getattr(value, field.name), field.type)
            for field in dataclasses.fields(value)
        )
    return False


def _checked_integrity_constant(value: PlutusData) -> None:
    """Python substitute for the on-chain integrity check during folding."""
    if not _matches_annotation(value, type(value)):
        raise TypeError("Datum does not match its annotated field types")
    value.to_cbor()


class ConstantExpressionSafetyValidator(NodeVisitor):
    """Reject Python constructs that can reach host capabilities during folding."""

    forbidden_nodes = (
        AsyncFor,
        AsyncFunctionDef,
        AsyncWith,
        Await,
        Delete,
        Global,
        Import,
        ImportFrom,
        Lambda,
        Nonlocal,
        Raise,
        Try,
        With,
        Yield,
        YieldFrom,
    ) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())

    def __init__(self, environment):
        self.environment = environment
        self.locally_defined_callables = set()

    def validate(self, node):
        self.locally_defined_callables.update(
            n.name for n in walk(node) if isinstance(n, (FunctionDef, ClassDef))
        )
        self.visit(node)

    def generic_visit(self, node):
        if isinstance(node, self.forbidden_nodes):
            raise UnsafeConstantExpression(
                f"{node.__class__.__name__} is unsafe during constant folding"
            )
        return super().generic_visit(node)

    def visit_Name(self, node):
        if node.id.startswith("__"):
            raise UnsafeConstantExpression(
                "Private runtime names are unavailable during constant folding"
            )

    def visit_Attribute(self, node):
        if node.attr.startswith("_"):
            raise UnsafeConstantExpression(
                "Private attributes are unavailable during constant folding"
            )
        root = node.value
        while isinstance(root, Attribute):
            root = root.value
        if isinstance(root, Name) and isinstance(
            self.environment.get(root.id), types.ModuleType
        ):
            raise UnsafeConstantExpression(
                "Module attributes are unavailable during constant folding"
            )
        if isinstance(node.ctx, Store):
            raise UnsafeConstantExpression(
                "Attribute mutation is unavailable during constant folding"
            )
        self.generic_visit(node)

    def visit_Subscript(self, node):
        if isinstance(node.ctx, Store):
            raise UnsafeConstantExpression(
                "Subscript mutation is unavailable during constant folding"
            )
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, Name):
            function = self.environment.get(node.func.id)
            if not (
                callable(function) or node.func.id in self.locally_defined_callables
            ):
                raise UnsafeConstantExpression(
                    f"Call to {node.func.id!r} is unavailable during constant folding"
                )
        elif not isinstance(node.func, Attribute):
            raise UnsafeConstantExpression(
                "Only direct calls are available during constant folding"
            )
        self.generic_visit(node)


class ShallowNameDefCollector(CompilingNodeVisitor):
    step = "Collecting occurring variable names"

    def __init__(self):
        self.vars = OrderedSet()

    def visit_Name(self, node: Name) -> None:
        if isinstance(node.ctx, Store):
            self.vars.add(node.id)

    def visit_ClassDef(self, node: ClassDef):
        self.vars.add(node.name)
        # ignore the content (i.e. attribute names) of class definitions

    def visit_FunctionDef(self, node: FunctionDef):
        self.vars.add(node.name)
        # ignore the recursive stuff


class DefinedTimesVisitor(CompilingNodeVisitor):
    step = "Collecting how often variables are written"

    def __init__(self):
        self.vars = defaultdict(int)

    def visit_For(self, node: For) -> None:
        # visit twice to have all names bumped to min 2 assignments
        self.generic_visit(node)
        self.generic_visit(node)
        return
        # TODO future items: use this together with guaranteed available
        # visit twice to have this name bumped to min 2 assignments
        self.visit(node.target)
        # visit the whole function
        self.generic_visit(node)

    def visit_While(self, node: While) -> None:
        # visit twice to have all names bumped to min 2 assignments
        self.generic_visit(node)
        self.generic_visit(node)
        return
        # TODO future items: use this together with guaranteed available

    def visit_If(self, node: If) -> None:
        # TODO future items: use this together with guaranteed available
        # visit twice to have all names bumped to min 2 assignments
        self.generic_visit(node)
        self.generic_visit(node)

    def visit_Name(self, node: Name) -> None:
        if isinstance(node.ctx, Store):
            self.vars[node.id] += 1

    def visit_ClassDef(self, node: ClassDef):
        self.vars[node.name] += 1
        # ignore the content (i.e. attribute names) of class definitions

    def visit_FunctionDef(self, node: FunctionDef):
        self.vars[node.name] += 1
        # visit arguments twice, they are generally assigned more than once
        for arg in node.args.args:
            self.vars[arg.arg] += 2
        self.generic_visit(node)

    def visit_Import(self, node: Import):
        for n in node.names:
            self.vars[n.asname or n.name.split(".")[0]] += 1

    def visit_ImportFrom(self, node: ImportFrom):
        for n in node.names:
            self.vars[n.asname or n.name] += 1


class OptimizeConstantFolding(CompilingNodeTransformer):
    step = "Constant folding"

    def __init__(self):
        self.scopes_visible = [
            OrderedSet(INITIAL_SCOPE.keys()).difference(SAFE_GLOBALS.keys())
        ]
        self.scopes_constants = [dict()]
        self.constants = OrderedSet()

    def enter_scope(self):
        self.scopes_visible.append(OrderedSet())
        self.scopes_constants.append(dict())

    def add_var_visible(self, var: str):
        self.scopes_visible[-1].add(var)

    def add_vars_visible(self, var: typing.Iterable[str]):
        self.scopes_visible[-1].update(var)

    def add_constant(self, var: str, value: typing.Any):
        self.scopes_constants[-1][var] = value

    def visible_vars(self):
        res_set = OrderedSet()
        for s in self.scopes_visible:
            res_set.update(s)
        return res_set

    def _constant_vars(self):
        res_d = {}
        for s in self.scopes_constants:
            res_d.update(s)
        return res_d

    def exit_scope(self):
        self.scopes_visible.pop(-1)
        self.scopes_constants.pop(-1)

    def _non_overwritten_globals(self):
        overwritten_vars = self.visible_vars()

        def err():
            raise ValueError("Was overwritten!")

        non_overwritten_globals = {
            k: (v if k not in overwritten_vars else err)
            for k, v in SAFE_GLOBALS.items()
        }
        non_overwritten_globals["__builtins__"] = {
            "__build_class__": builtins.__build_class__,
        }
        non_overwritten_globals["__name__"] = "opshin_constant_folding"
        return non_overwritten_globals

    def _validate(self, node, environment):
        ConstantExpressionSafetyValidator(environment).validate(node)

    def update_constants(self, node):
        a = self._non_overwritten_globals()
        a.update(self._constant_vars())
        g = a
        l = {}
        try:
            self._validate(node, {**g, **l})
            with _constant_evaluation_budget():
                exec(unparse(node), g, l)
        except Exception as e:
            OPSHIN_LOGGER.debug(e)
        else:
            # the class is defined and added to the globals
            self.scopes_constants[-1].update(l)

    def visit_Module(self, node: Module) -> Module:
        self.enter_scope()
        def_vars_collector = ShallowNameDefCollector()
        def_vars_collector.visit(node)
        def_vars = def_vars_collector.vars
        self.add_vars_visible(def_vars)

        constant_collector = DefinedTimesVisitor()
        constant_collector.visit(node)
        constants = constant_collector.vars
        # if it is only assigned exactly once, it must be a constant (due to immutability)
        self.constants = {c for c, i in constants.items() if i == 1}

        res = self.generic_visit(node)
        self.exit_scope()
        return res

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        self.add_var_visible(node.name)
        if node.name in self.constants:
            a = self._non_overwritten_globals()
            a.update(self._constant_vars())
            g = a
            try:
                self._validate(node, g)
                # we need to pass the global dict as local dict here to make closures possible (rec functions)
                with _constant_evaluation_budget():
                    exec(unparse(node), g, g)
            except Exception as e:
                OPSHIN_LOGGER.debug(e)
            else:
                # the class is defined and added to the globals
                self.scopes_constants[-1][node.name] = g[node.name]

        self.enter_scope()
        self.add_vars_visible(arg.arg for arg in node.args.args)
        def_vars_collector = ShallowNameDefCollector()
        for s in node.body:
            def_vars_collector.visit(s)
        def_vars = def_vars_collector.vars
        self.add_vars_visible(def_vars)

        res_node = self.generic_visit(node)
        self.exit_scope()
        return res_node

    def visit_ClassDef(self, node: ClassDef):
        if node.name in self.constants:
            self.update_constants(node)
        return node

    def visit_ImportFrom(self, node: ImportFrom):
        if node.module not in TRUSTED_IMPORTS:
            return node
        module = importlib.import_module(node.module)
        trusted_names = TRUSTED_IMPORTS[node.module]
        for imported_name in node.names:
            if imported_name.name == "*":
                for name in trusted_names:
                    self.add_constant(name, getattr(module, name))
            elif imported_name.name in trusted_names:
                bound_name = imported_name.asname or imported_name.name
                imported_value = getattr(module, imported_name.name)
                if (
                    node.module == "opshin.std.integrity"
                    and imported_name.name == "check_integrity"
                ):
                    imported_value = _checked_integrity_constant
                self.add_constant(bound_name, imported_value)
        return node

    def visit_Import(self, node: Import):
        # Module objects expose broad APIs. They are intentionally not made
        # available to compile-time evaluation.
        return node

    def visit_Assign(self, node: Assign):
        if len(node.targets) != 1:
            return node
        target = node.targets[0]
        if not isinstance(target, Name):
            return node

        if target.id in self.constants:
            self.update_constants(node)
        node.value = self.visit(node.value)
        return node

    def visit_AnnAssign(self, node: AnnAssign):
        target = node.target
        if not isinstance(target, Name):
            return node

        if target.id in self.constants:
            self.update_constants(node)
        node.value = self.visit(node.value)
        return node

    def generic_visit(self, node: AST):
        node = super().generic_visit(node)
        if not isinstance(node, expr):
            # only evaluate expressions, not statements
            return node
        if isinstance(node, Constant):
            # prevents unnecessary computations
            return node
        try:
            node_source = unparse(node)
        except Exception as e:
            OPSHIN_LOGGER.debug("Error when trying to unparse node: %s", e)
            return node
        if "print(" in node_source:
            # do not optimize away print statements
            return node
        try:
            # we add preceding constant plutusdata definitions here!
            g = self._non_overwritten_globals()
            l = self._constant_vars()
            self._validate(node, {**g, **l})
            with _constant_evaluation_budget():
                node_eval = eval(node_source, g, l)
        except Exception as e:
            OPSHIN_LOGGER.debug("Error trying to evaluate node: %s", e)
            return node

        if any(
            isinstance(node_eval, t)
            for t in ACCEPTED_ATOMIC_TYPES + [list, dict, PlutusData]
        ) and not (node_eval == [] or node_eval == {}):
            new_node = Constant(node_eval, None)
            copy_location(new_node, node)
            return new_node
        return node
