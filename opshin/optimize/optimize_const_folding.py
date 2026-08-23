import copy
import typing
from collections import defaultdict
import logging

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
    classmethod,
    compile,
    complex,
    delattr,
    dict,
    dir,
    divmod,
    enumerate,
    filter,
    float,
    format,
    frozenset,
    getattr,
    hasattr,
    hash,
    hex,
    id,
    input,
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
    object,
    oct,
    open,
    ord,
    pow,
    print,
    property,
    range,
    repr,
    reversed,
    round,
    set,
    setattr,
    slice,
    sorted,
    staticmethod,
    str,
    sum,
    super,
    tuple,
    type,
    vars,
    zip,
]
SAFE_GLOBALS = {x.__name__: x for x in SAFE_GLOBALS_LIST}

# constants of these types may be mutated in place by method calls (append, insert,
# pop, update, ...). Evaluating such calls at compile time would apply the mutation
# to a copy of the constant (or lose it entirely), silently changing the program.
MUTABLE_CONSTANT_TYPES = (list, dict, set, bytearray)


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
            self.vars[n] += 1

    def visit_ImportFrom(self, node: ImportFrom):
        for n in node.names:
            self.vars[n] += 1


class OptimizeConstantFolding(CompilingNodeTransformer):
    step = "Constant folding"

    def __init__(self):
        self.scopes_visible = [
            OrderedSet(INITIAL_SCOPE.keys()).difference(SAFE_GLOBALS.keys())
        ]
        self.scopes_constants = [dict()]
        self.constants = OrderedSet()
        # names of user-defined functions that must never be executed at compile
        # time because they may have side effects (e.g. printing)
        self.impure_functions = OrderedSet()

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
        return non_overwritten_globals

    def update_constants(self, node):
        a = self._non_overwritten_globals()
        a.update(self._constant_vars())
        g = a
        l = {}
        try:
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

    def _may_have_side_effects(self, node: FunctionDef) -> bool:
        """Best-effort check whether executing the given function definition
        could have side effects (e.g. printing). Such functions must not be
        executed at compile time, their effects would silently be lost."""
        for subnode in walk(node):
            if isinstance(subnode, Call) and isinstance(subnode.func, Name):
                if (
                    subnode.func.id == "print"
                    or subnode.func.id in self.impure_functions
                ):
                    return True
        return False

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        self.add_var_visible(node.name)
        if node.name in self.constants and self._may_have_side_effects(node):
            # never execute functions with potential side effects at compile time
            self.impure_functions.add(node.name)
        elif node.name in self.constants:
            a = self._non_overwritten_globals()
            a.update(self._constant_vars())
            g = a
            try:
                # we need to pass the global dict as local dict here to make closures possible (rec functions)
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
        if all(n in self.constants for n in node.names):
            self.update_constants(node)
        return node

    def visit_Import(self, node: Import):
        if all(n in self.constants for n in node.names):
            self.update_constants(node)
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

    def _contains_call_on_mutable_constant(self, node: AST) -> bool:
        """Checks whether the node contains a method call on a mutable constant
        (e.g. ``l.append(x)``, ``d.pop()``). Evaluating such calls at compile time
        would apply the mutation to a throwaway copy of the constant while the
        original statement is replaced by the (discarded) return value, silently
        changing the program. Such nodes are left untouched so downstream stages
        either compile them correctly or reject them with a proper error."""
        for subnode in walk(node):
            if isinstance(subnode, Call) and isinstance(subnode.func, Attribute):
                receiver = subnode.func.value
                if isinstance(receiver, Constant) and isinstance(
                    receiver.value, MUTABLE_CONSTANT_TYPES
                ):
                    return True
        return False

    def _snapshot_mutable_constants(self):
        """Snapshots the values of all mutable constants to detect (and undo)
        mutations performed while evaluating a candidate expression."""
        res = {}
        for scope in self.scopes_constants:
            for k, v in scope.items():
                if isinstance(v, MUTABLE_CONSTANT_TYPES) and id(v) not in res:
                    try:
                        res[id(v)] = (v, copy.deepcopy(v))
                    except Exception as e:
                        OPSHIN_LOGGER.debug(
                            "Could not snapshot constant %s for mutation detection: %s",
                            k,
                            e,
                        )
        return res

    def _constants_mutated(self, snapshot) -> bool:
        return any(
            obj is not snap and repr(obj) != repr(snap)
            for obj, snap in snapshot.values()
        )

    def _restore_mutable_constants(self, snapshot) -> None:
        for obj, snap in snapshot.values():
            if repr(obj) == repr(snap):
                continue
            # restore in place to keep aliases of the same object consistent
            if isinstance(obj, list):
                obj[:] = snap
            elif isinstance(obj, dict):
                obj.clear()
                obj.update(snap)
            elif isinstance(obj, set):
                obj.clear()
                obj.update(snap)
            elif isinstance(obj, bytearray):
                obj[:] = snap

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
        if self._contains_call_on_mutable_constant(node):
            # never evaluate expressions that mutate constants at compile time,
            # leave them untouched for the following compilation steps
            return node
        snapshot = self._snapshot_mutable_constants()
        try:
            # we add preceding constant plutusdata definitions here!
            g = self._non_overwritten_globals()
            l = self._constant_vars()
            node_eval = eval(node_source, g, l)
        except Exception as e:
            OPSHIN_LOGGER.debug("Error trying to evaluate node: %s", e)
            self._restore_mutable_constants(snapshot)
            return node

        if self._constants_mutated(snapshot):
            # evaluating this expression mutated a constant (e.g. through a call
            # to a user-defined function with side effects), so it must neither be
            # folded away nor may the constants table keep the mutated value
            OPSHIN_LOGGER.warning(
                "Not constant folding %s because evaluating it has side effects",
                node_source,
            )
            self._restore_mutable_constants(snapshot)
            return node

        if any(
            isinstance(node_eval, t)
            for t in ACCEPTED_ATOMIC_TYPES + [list, dict, PlutusData]
        ) and not (node_eval == [] or node_eval == {}):
            new_node = Constant(node_eval, None)
            copy_location(new_node, node)
            return new_node
        return node
