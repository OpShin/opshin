import ast
import itertools
import typing
from dataclasses import dataclass

from ..rewrite.rewrite_import_integrity_check import IntegrityCheckImpl
from ..type_impls import (
    AnyType,
    BoolType,
    ByteStringType,
    DataInstanceType,
    DictType,
    FunctionType,
    InstanceType,
    IntegerType,
    ListType,
    PolymorphicFunctionInstanceType,
    RecordType,
    StringType,
    UnionType,
)
from ..util import CompilingNodeTransformer, OPSHIN_LOGGER
from ..typed_ast import RawPlutoExpr

MAX_SUMMARIZED_PARAMETERS = 9


@dataclass(frozen=True)
class FunctionIntegritySummary:
    return_integrity_checked: bool
    integrity_checked_parameters: frozenset[int]


def _requires_integrity_check(typ) -> bool:
    if isinstance(typ, DataInstanceType):
        return True
    if not isinstance(typ, InstanceType):
        return False
    return isinstance(typ.typ, (AnyType, UnionType, RecordType, ListType, DictType))


def is_integrity_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func.typ, PolymorphicFunctionInstanceType)
        and isinstance(node.func.typ.polymorphic_function, IntegrityCheckImpl)
    )


def _name_read_validates_value(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Name)
        and isinstance(node.typ, DataInstanceType)
        and isinstance(
            node.typ.typ, (IntegerType, ByteStringType, StringType, BoolType)
        )
    )


def _atomic_data_type(typ) -> bool:
    if isinstance(typ, InstanceType):
        typ = typ.typ
    return isinstance(typ, (IntegerType, ByteStringType, StringType, BoolType))


def positively_validated_atomic_names(node: ast.AST) -> set[str]:
    """Names whose complete atomic representation is checked on every true path."""

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and getattr(node.func, "orig_id", None) == "~bool"
    ):
        return positively_validated_atomic_names(node.args[0])
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and getattr(node.func, "orig_id", None) == "isinstance"
        and isinstance(node.args[0], ast.Name)
    ):
        return {node.args[0].id} if _atomic_data_type(node.args[1].typ) else set()
    if isinstance(node, ast.BoolOp):
        validated = [positively_validated_atomic_names(value) for value in node.values]
        if isinstance(node.op, ast.And):
            return set().union(*validated)
        if isinstance(node.op, ast.Or) and validated:
            return set.intersection(*validated)
    return set()


def _guaranteed_validated_names(node: typing.Optional[ast.AST]) -> set[str]:
    """Names decoded on every successful evaluation path through an expression."""

    if node is None:
        return set()
    if _name_read_validates_value(node):
        return {node.id}
    if isinstance(node, ast.BoolOp):
        return _guaranteed_validated_names(node.values[0])
    if isinstance(node, ast.IfExp):
        return _guaranteed_validated_names(node.test) | _guaranteed_validated_names(
            node.body
        ).intersection(_guaranteed_validated_names(node.orelse))
    if isinstance(node, ast.Compare):
        guaranteed = _guaranteed_validated_names(node.left)
        if node.comparators:
            guaranteed |= _guaranteed_validated_names(node.comparators[0])
        return guaranteed
    if isinstance(node, (ast.ListComp, ast.DictComp)):
        if not node.generators:
            return set()
        return _guaranteed_validated_names(node.generators[0].iter)
    if isinstance(
        node,
        (
            ast.Call,
            ast.BinOp,
            ast.UnaryOp,
            ast.Attribute,
            ast.Subscript,
            ast.List,
            ast.Tuple,
            ast.Dict,
            ast.Slice,
            ast.JoinedStr,
            ast.FormattedValue,
        ),
    ):
        guaranteed = set()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                guaranteed.update(_guaranteed_validated_names(child))
        return guaranteed
    return set()


def _user_function_id(node: ast.Call) -> typing.Optional[str]:
    func_typ = node.func.typ
    if not isinstance(func_typ, InstanceType) or not isinstance(
        func_typ.typ, FunctionType
    ):
        return None
    return func_typ.typ.function_id


def _merge_environments(*envs: dict[str, bool]) -> dict[str, bool]:
    if not envs:
        return {}
    names = set().union(*(env.keys() for env in envs))
    return {name: all(env.get(name, False) for env in envs) for name in names}


def _source_label(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return getattr(node, "orig_id", node.id)
    if isinstance(node, ast.Attribute):
        return f"{_source_label(node.value)}.{node.attr}"
    return ast.unparse(node)


class _FunctionFlowAnalyzer:
    def __init__(
        self,
        summaries: dict[tuple[str, tuple[bool, ...]], FunctionIntegritySummary],
        functions: dict[str, ast.FunctionDef],
        annotate: bool,
        warn_unchecked_uses: bool = False,
    ):
        self.summaries = summaries
        self.functions = functions
        self.annotate = annotate
        self.warn_unchecked_uses = warn_unchecked_uses
        self.returns: list[tuple[bool, dict[str, bool]]] = []

    def _mark(self, node: ast.AST, integrity_checked: bool) -> bool:
        # BuiltinData/Anything deliberately carries no schema. Even a value
        # produced by checked code requires another integrity check once widened to this type.
        if isinstance(node.typ, InstanceType) and isinstance(node.typ.typ, AnyType):
            integrity_checked = False
        if self.annotate:
            node.integrity_checked = integrity_checked
        return integrity_checked

    def expression(self, node: typing.Optional[ast.AST], env: dict[str, bool]) -> bool:
        if node is None:
            return True
        if isinstance(node, ast.Name):
            integrity_checked = env.get(
                node.id,
                not _requires_integrity_check(node.typ),
            )
            self._mark(
                node,
                integrity_checked,
            )
            return integrity_checked or _name_read_validates_value(node)
        if isinstance(node, ast.Constant):
            return self._mark(
                node,
                not _requires_integrity_check(node.typ),
            )
        if isinstance(node, RawPlutoExpr):
            return self._mark(
                node,
                not _requires_integrity_check(node.typ),
            )
        if isinstance(node, ast.Attribute):
            owner_integrity_checked = self.expression(node.value, env)
            result_is_payload = isinstance(node.typ, InstanceType) and isinstance(
                node.typ.typ, AnyType
            )
            return self._mark(node, owner_integrity_checked and not result_is_payload)
        if isinstance(node, ast.Subscript):
            source_integrity_checked = self.expression(node.value, env)
            self.expression(node.slice, env)
            result_is_payload = isinstance(node.typ, InstanceType) and isinstance(
                node.typ.typ, AnyType
            )
            return self._mark(node, source_integrity_checked and not result_is_payload)
        if isinstance(node, ast.IfExp):
            self.expression(node.test, env)
            body_integrity_checked = self.expression(node.body, dict(env))
            else_integrity_checked = self.expression(node.orelse, dict(env))
            return self._mark(
                node,
                body_integrity_checked and else_integrity_checked,
            )
        if isinstance(node, ast.BoolOp):
            values = [self.expression(value, env) for value in node.values]
            return self._mark(node, all(values))
        if isinstance(node, (ast.List, ast.Tuple)):
            values = [self.expression(value, env) for value in node.elts]
            return self._mark(node, all(values))
        if isinstance(node, ast.Dict):
            children = [key for key in node.keys if key is not None] + list(node.values)
            values = [self.expression(value, env) for value in children]
            return self._mark(node, all(values))
        if isinstance(node, ast.Compare):
            operands = [node.left] + list(node.comparators)
            operand_checks = [self.expression(operand, env) for operand in operands]
            if self.warn_unchecked_uses:
                warned = set()
                for index, operator in enumerate(node.ops):
                    if not isinstance(operator, (ast.Eq, ast.NotEq, ast.In, ast.NotIn)):
                        continue
                    for operand_index in (index, index + 1):
                        operand = operands[operand_index]
                        if operand_checks[operand_index] or operand_index in warned:
                            continue
                        warned.add(operand_index)
                        label = _source_label(operand)
                        OPSHIN_LOGGER.warning(
                            f"Integrity-unchecked value '{label}' is used in a "
                            "non-validating comparison; malformed data can affect "
                            "the result without being rejected."
                        )
            return self._mark(node, True)
        if isinstance(node, ast.ListComp):
            comp_env = dict(env)
            for generator in node.generators:
                item_integrity_checked = self.expression(generator.iter, comp_env)
                self._assign(generator.target, item_integrity_checked, comp_env)
                for condition in generator.ifs:
                    self.expression(condition, comp_env)
            return self._mark(node, self.expression(node.elt, comp_env))
        if isinstance(node, ast.DictComp):
            comp_env = dict(env)
            for generator in node.generators:
                item_integrity_checked = self.expression(generator.iter, comp_env)
                self._assign(generator.target, item_integrity_checked, comp_env)
                for condition in generator.ifs:
                    self.expression(condition, comp_env)
            key_integrity_checked = self.expression(node.key, comp_env)
            value_integrity_checked = self.expression(node.value, comp_env)
            return self._mark(node, key_integrity_checked and value_integrity_checked)
        if isinstance(node, ast.Call):
            self.expression(node.func, env)
            argument_checks = tuple(self.expression(arg, env) for arg in node.args)
            if is_integrity_call(node):
                return self._mark(node, True)
            function_id = _user_function_id(node)
            if function_id in self.functions:
                function = self.functions[function_id]
                normalized = tuple(
                    integrity_checked or not _requires_integrity_check(parameter.typ)
                    for integrity_checked, parameter in zip(
                        argument_checks, function.args.args
                    )
                )
                summary = self.summaries.get(
                    (function_id, normalized),
                    FunctionIntegritySummary(False, frozenset()),
                )
                return self._mark(node, summary.return_integrity_checked)
            func_typ = node.func.typ
            is_constructor = (
                isinstance(func_typ, InstanceType)
                and isinstance(func_typ.typ, FunctionType)
                and func_typ.typ.function_id is None
                and _requires_integrity_check(node.typ)
            )
            return self._mark(node, all(argument_checks) if is_constructor else True)

        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self.expression(child, env)
        # Operators and compiler builtins either produce a valid value or fail.
        return self._mark(node, True)

    def _assign(
        self, target: ast.AST, integrity_checked: bool, env: dict[str, bool]
    ) -> None:
        if isinstance(target, ast.Name):
            env[target.id] = integrity_checked
            if self.annotate:
                target.integrity_checked = integrity_checked
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._assign(element, integrity_checked, env)

    def _apply_call_postconditions(self, node: ast.AST, env: dict[str, bool]) -> None:
        if not isinstance(node, ast.Call):
            return
        if is_integrity_call(node):
            if len(node.args) == 1 and isinstance(node.args[0], ast.Name):
                env[node.args[0].id] = True
            return
        function_id = _user_function_id(node)
        if function_id not in self.functions:
            return
        function = self.functions[function_id]
        argument_checks = tuple(
            self.expression(argument, env) for argument in node.args
        )
        normalized = tuple(
            integrity_checked or not _requires_integrity_check(parameter.typ)
            for integrity_checked, parameter in zip(argument_checks, function.args.args)
        )
        summary = self.summaries.get(
            (function_id, normalized), FunctionIntegritySummary(False, frozenset())
        )
        for index in summary.integrity_checked_parameters:
            if index < len(node.args) and isinstance(node.args[index], ast.Name):
                env[node.args[index].id] = True

    def _apply_expression_postconditions(
        self, node: ast.AST, env: dict[str, bool]
    ) -> None:
        for name in _guaranteed_validated_names(node):
            env[name] = True
        self._apply_call_postconditions(node, env)

    def statement(
        self, node: ast.stmt, env: dict[str, bool]
    ) -> tuple[dict[str, bool], bool]:
        if isinstance(node, ast.Assign):
            integrity_checked = self.expression(node.value, env)
            self._apply_expression_postconditions(node.value, env)
            for target in node.targets:
                self._assign(target, integrity_checked, env)
            return env, True
        if isinstance(node, ast.AnnAssign):
            integrity_checked = self.expression(node.value, env)
            self._apply_expression_postconditions(node.value, env)
            self._assign(node.target, integrity_checked, env)
            return env, True
        if isinstance(node, ast.Expr):
            # Docstrings and other bare string literals are retained as
            # untyped syntax by type inference, but have no runtime value in
            # the compiled program.
            if isinstance(node.value, ast.Constant) and isinstance(
                node.value.value, str
            ):
                return env, True
            self.expression(node.value, env)
            self._apply_expression_postconditions(node.value, env)
            return env, True
        if isinstance(node, ast.Return):
            integrity_checked = self.expression(node.value, env)
            self._apply_expression_postconditions(node.value, env)
            self.returns.append((integrity_checked, dict(env)))
            return env, False
        if isinstance(node, ast.If):
            self.expression(node.test, env)
            self._apply_expression_postconditions(node.test, env)
            body_input = dict(env)
            for name in positively_validated_atomic_names(node.test):
                body_input[name] = True
            body_env, body_falls = self.sequence(node.body, body_input)
            else_env, else_falls = self.sequence(node.orelse, dict(env))
            fallthrough = [
                branch_env
                for branch_env, falls in (
                    (body_env, body_falls),
                    (else_env, else_falls),
                )
                if falls
            ]
            return (
                _merge_environments(*fallthrough) if fallthrough else dict(env),
                bool(fallthrough),
            )
        if isinstance(node, (ast.For, ast.While)):
            entry = dict(env)
            loop_env = dict(entry)
            while True:
                iteration_env = dict(loop_env)
                if isinstance(node, ast.For):
                    item_integrity_checked = self.expression(node.iter, iteration_env)
                    self._apply_expression_postconditions(node.iter, iteration_env)
                    self._assign(node.target, item_integrity_checked, iteration_env)
                else:
                    self.expression(node.test, iteration_env)
                    self._apply_expression_postconditions(node.test, iteration_env)
                previous_returns = len(self.returns)
                body_env, body_falls = self.sequence(node.body, iteration_env)
                del self.returns[previous_returns:]
                next_env = _merge_environments(entry, body_env if body_falls else entry)
                if next_env == loop_env:
                    break
                loop_env = next_env
            # Analyze once with the fixed point, retaining returns and annotations.
            iteration_env = dict(loop_env)
            if isinstance(node, ast.For):
                item_integrity_checked = self.expression(node.iter, iteration_env)
                self._apply_expression_postconditions(node.iter, iteration_env)
                self._assign(node.target, item_integrity_checked, iteration_env)
            else:
                self.expression(node.test, iteration_env)
                self._apply_expression_postconditions(node.test, iteration_env)
            self.sequence(node.body, iteration_env)
            return self.sequence(node.orelse, loop_env)
        if isinstance(node, ast.Assert):
            self.expression(node.test, env)
            self._apply_expression_postconditions(node.test, env)
            self.expression(node.msg, env)
            return env, True
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Pass)):
            return env, True
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self.expression(child, env)
        return env, bool(getattr(node, "can_fall_through", True))

    def sequence(
        self, body: typing.Iterable[ast.stmt], env: dict[str, bool]
    ) -> tuple[dict[str, bool], bool]:
        current = dict(env)
        falls = True
        for statement in body:
            if statement is None or not falls:
                continue
            current, falls = self.statement(statement, current)
        return current, falls

    def function_summary(
        self, function: ast.FunctionDef, parameter_checks: tuple[bool, ...]
    ) -> FunctionIntegritySummary:
        env = {
            argument.arg: integrity_checked
            for argument, integrity_checked in zip(function.args.args, parameter_checks)
        }
        final_env, falls = self.sequence(function.body, env)
        exits = list(self.returns)
        if falls:
            exits.append((True, final_env))
        if not exits:
            return FunctionIntegritySummary(False, frozenset())
        integrity_checked_parameters = frozenset(
            index
            for index, argument in enumerate(function.args.args)
            if all(exit_env.get(argument.arg, True) for _, exit_env in exits)
        )
        return FunctionIntegritySummary(
            all(return_integrity_checked for return_integrity_checked, _ in exits),
            integrity_checked_parameters,
        )


class AnalyzeIntegrity(CompilingNodeTransformer):
    """Annotate expressions with conservative runtime data-integrity facts."""

    step = "Analyzing runtime data integrity"

    def __init__(self, validator_function_name: str = "validator"):
        self.validator_function_name = validator_function_name

    @staticmethod
    def _integrity_checked_validator_parameter(
        function: ast.FunctionDef, argument
    ) -> bool:
        if not isinstance(argument.typ, InstanceType) or not isinstance(
            argument.typ.typ, RecordType
        ):
            return False
        return argument.typ.typ.record.orig_name == "ScriptContext"

    def visit_Module(self, node: ast.Module) -> ast.Module:
        functions = {
            function.function_id: function
            for function in ast.walk(node)
            if isinstance(function, ast.FunctionDef)
            and getattr(function, "function_id", None) is not None
        }
        summaries: dict[tuple[str, tuple[bool, ...]], FunctionIntegritySummary] = {}
        configurations: dict[str, list[tuple[bool, ...]]] = {}
        for function_id, function in functions.items():
            if len(function.args.args) > MAX_SUMMARIZED_PARAMETERS:
                configurations[function_id] = []
                continue
            relevant = [
                index
                for index, argument in enumerate(function.args.args)
                if _requires_integrity_check(argument.typ)
            ]
            configs = []
            for values in itertools.product((False, True), repeat=len(relevant)):
                config = [True] * len(function.args.args)
                for index, integrity_checked in zip(relevant, values):
                    config[index] = integrity_checked
                configs.append(tuple(config))
            configurations[function_id] = configs
            for config in configs:
                summaries[(function_id, config)] = FunctionIntegritySummary(
                    False, frozenset()
                )

        while True:
            updated = dict(summaries)
            for function_id, configs in configurations.items():
                for config in configs:
                    analyzer = _FunctionFlowAnalyzer(summaries, functions, False)
                    updated[(function_id, config)] = analyzer.function_summary(
                        functions[function_id], config
                    )
            if updated == summaries:
                break
            summaries = updated

        for function in functions.values():
            initial = tuple(
                not _requires_integrity_check(argument.typ)
                or (
                    function.orig_name == self.validator_function_name
                    and self._integrity_checked_validator_parameter(function, argument)
                )
                for argument in function.args.args
            )
            analyzer = _FunctionFlowAnalyzer(
                summaries,
                functions,
                True,
                warn_unchecked_uses=(
                    function.orig_name == self.validator_function_name
                ),
            )
            analyzer.function_summary(function, initial)

        node.integrity_summaries = summaries
        return node
