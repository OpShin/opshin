import ast
import typing
from copy import copy

from ..type_impls import (
    AnyType,
    ByteStringType,
    DataInstanceType,
    InstanceType,
    IntegerType,
    ListType,
    Type,
    UnionType,
    strip_data_instance_type,
)
from ..type_inference import TypeCheckVisitor
from ..typed_ast import TypedAssign
from ..typed_util import ScopedSequenceNodeTransformer

# Minimum reads for (terminal arm, fallthrough arm). A fallthrough arm also has
# to convert the narrowed value back to Data before entering its continuation.
# These conservative cutoffs include the extra Let/Delay/Force bookkeeping.
READ_THRESHOLDS = {
    ListType: (3, 4),
    IntegerType: (6, 9),
    ByteStringType: (6, 9),
}


class _TestNameCollector(ast.NodeVisitor):
    def __init__(self):
        self.names: typing.Dict[str, ast.Name] = {}

    def visit_Name(self, node: ast.Name):
        if hasattr(node, "typ"):
            self.names.setdefault(node.id, node)


class _AccessCollector(ast.NodeVisitor):
    """Detect accesses that cannot safely share a narrowed representation."""

    def __init__(self, name: str):
        self.name = name
        self.unsafe = False

    def _mark_if_captured(self, node: ast.AST):
        if any(
            isinstance(child, ast.Name) and child.id == self.name
            for child in ast.walk(node)
        ):
            self.unsafe = True

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._mark_if_captured(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._mark_if_captured(node)

    def visit_Call(self, node: ast.Call):
        if (
            isinstance(node.func, ast.Name)
            and getattr(node.func, "orig_id", None) == "isinstance"
            and any(
                isinstance(child, ast.Name) and child.id == self.name
                for arg in node.args
                for child in ast.walk(arg)
            )
        ):
            self.unsafe = True
            return
        self.generic_visit(node)


class _ExpectedReadCounter:
    """Estimate dynamically executed reads using source-level cost hints."""

    DEFAULT_BRANCH_PROBABILITY = 0.5
    DEFAULT_ITERATIONS = 1.0

    def __init__(self, name: str):
        self.name = name

    def expression(self, node: typing.Optional[ast.AST]) -> float:
        if node is None:
            return 0.0
        if isinstance(node, ast.Name):
            return float(node.id == self.name and isinstance(node.ctx, ast.Load))
        if isinstance(node, ast.IfExp):
            probability = self.DEFAULT_BRANCH_PROBABILITY
            return (
                self.expression(node.test)
                + probability * self.expression(node.body)
                + (1.0 - probability) * self.expression(node.orelse)
            )
        if isinstance(node, ast.BoolOp):
            probability_reached = 1.0
            reads = 0.0
            for value in node.values:
                reads += probability_reached * self.expression(value)
                probability_reached *= self.DEFAULT_BRANCH_PROBABILITY
            return reads
        return sum(self.expression(child) for child in ast.iter_child_nodes(node))

    def sequence(self, body: typing.List[ast.stmt]) -> typing.Tuple[float, float]:
        reads = 0.0
        probability_reached = 1.0
        for statement in body:
            statement_reads, statement_fallthrough = self.statement(statement)
            reads += probability_reached * statement_reads
            probability_reached *= statement_fallthrough
        return reads, probability_reached

    def statement(self, node: ast.stmt) -> typing.Tuple[float, float]:
        if isinstance(node, ast.If):
            probability = getattr(
                node, "branch_probability", self.DEFAULT_BRANCH_PROBABILITY
            )
            body_reads, body_fallthrough = self.sequence(node.body)
            else_reads, else_fallthrough = self.sequence(node.orelse)
            return (
                self.expression(node.test)
                + probability * body_reads
                + (1.0 - probability) * else_reads,
                probability * body_fallthrough + (1.0 - probability) * else_fallthrough,
            )
        if isinstance(node, (ast.For, ast.While)):
            iterations = getattr(node, "iterations", self.DEFAULT_ITERATIONS)
            body_reads, body_fallthrough = self.sequence(node.body)
            else_reads, else_fallthrough = self.sequence(node.orelse)
            completes = body_fallthrough**iterations
            header_reads = (
                self.expression(node.iter)
                if isinstance(node, ast.For)
                else (iterations + 1.0) * self.expression(node.test)
            )
            return (
                header_reads + iterations * body_reads + completes * else_reads,
                completes * else_fallthrough,
            )
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            return 0.0, 1.0
        return self.expression(node), float(getattr(node, "can_fall_through", True))


class _RepresentationRewriter(ScopedSequenceNodeTransformer):
    def __init__(self, representations: typing.Dict[str, InstanceType]):
        self.representations = representations

    def visit_FunctionDef(self, node: ast.FunctionDef):
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        return node

    def visit_Name(self, node: ast.Name):
        typ = self.representations.get(node.id)
        if typ is None or not hasattr(node, "typ"):
            return node
        rewritten = copy(node)
        rewritten.typ = typ
        return rewritten


def _assignment(
    template: ast.Name,
    target_typ: Type,
    value_typ: Type,
) -> TypedAssign:
    target = copy(template)
    target.ctx = ast.Store()
    target.typ = target_typ
    value = copy(template)
    value.ctx = ast.Load()
    value.typ = value_typ
    return TypedAssign(targets=[target], value=value)


class OptimizeSelectiveNarrowing(ScopedSequenceNodeTransformer):
    """Use one builtin representation throughout a narrowed control-flow arm.

    The rebind deliberately keeps the original variable name. OpShin's code
    generator therefore sees ordinary branch/loop-carried state, rather than a
    fresh local assignment that it would incorrectly expect to exist before the
    branch. A fallthrough arm converts the value back to its data-backed type.

    Expected read counts assume equally likely ``if`` branches and one loop
    iteration unless source comments provide ``branch-probability`` or
    ``iterations`` hints.
    """

    step = "Caching repeatedly used narrowed values"

    def __init__(self, allow_isinstance_anything: bool = False):
        self.allow_isinstance_anything = allow_isinstance_anything

    @staticmethod
    def _eligible_target(typ: Type) -> typing.Optional[InstanceType]:
        target = typ if isinstance(typ, InstanceType) else InstanceType(typ)
        target = strip_data_instance_type(target)
        if not isinstance(target, InstanceType) or isinstance(
            target.typ, (AnyType, UnionType)
        ):
            return None
        if not any(isinstance(target.typ, kind) for kind in READ_THRESHOLDS):
            return None
        return target

    def _rewrite_arm(
        self,
        body: typing.List[ast.stmt],
        typechecks: typing.Dict[str, Type],
        test_names: typing.Dict[str, ast.Name],
        can_fall_through: bool,
    ) -> typing.List[ast.stmt]:
        selected: typing.Dict[str, typing.Tuple[ast.Name, Type, InstanceType]] = {}
        for name, narrowed_typ in typechecks.items():
            template = test_names.get(name)
            if template is None:
                continue
            source_typ = template.typ
            if not (
                isinstance(source_typ, DataInstanceType)
                or (
                    isinstance(source_typ, InstanceType)
                    and isinstance(source_typ.typ, (AnyType, UnionType))
                )
            ):
                continue
            target_typ = self._eligible_target(narrowed_typ)
            if target_typ is None:
                continue
            accesses = _AccessCollector(name)
            for statement in body:
                accesses.visit(statement)
            expected_reads, _ = _ExpectedReadCounter(name).sequence(body)
            thresholds = next(
                limits
                for kind, limits in READ_THRESHOLDS.items()
                if isinstance(target_typ.typ, kind)
            )
            threshold = thresholds[1 if can_fall_through else 0]
            if accesses.unsafe or expected_reads < threshold:
                continue
            selected[name] = (template, source_typ, target_typ)

        if not selected:
            return self.visit_sequence(list(body))

        representations = {
            name: target_typ for name, (_, _, target_typ) in selected.items()
        }
        rewritten = _RepresentationRewriter(representations).visit_sequence(list(body))
        rewritten = self.visit_sequence(rewritten)
        prefix = [
            _assignment(template, target_typ, DataInstanceType(target_typ.typ))
            for template, _, target_typ in selected.values()
        ]
        suffix = []
        if can_fall_through:
            suffix = [
                _assignment(template, source_typ, target_typ)
                for template, source_typ, target_typ in selected.values()
            ]
        return prefix + rewritten + suffix

    def _visit_conditional(self, node):
        rewritten = copy(node)
        rewritten.test = self.visit(node.test)
        typechecks, inverse_typechecks = TypeCheckVisitor(
            self.allow_isinstance_anything
        ).visit(rewritten.test)
        names = _TestNameCollector()
        names.visit(rewritten.test)
        rewritten.body = self._rewrite_arm(
            list(node.body),
            typechecks,
            names.names,
            getattr(node, "body_can_fall_through", True),
        )
        rewritten.orelse = self._rewrite_arm(
            list(node.orelse),
            inverse_typechecks,
            names.names,
            getattr(node, "orelse_can_fall_through", True),
        )
        return rewritten

    def visit_If(self, node: ast.If):
        return self._visit_conditional(node)

    def visit_While(self, node: ast.While):
        return self._visit_conditional(node)
