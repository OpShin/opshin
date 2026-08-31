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


class _ContinuationUseCollector(ast.NodeVisitor):
    """Conservatively detect whether a continuation may need a name."""

    def __init__(self, name: str):
        self.name = name
        self.used = False

    def visit_Name(self, node: ast.Name):
        if node.id == self.name and isinstance(node.ctx, ast.Load):
            self.used = True

    def visit_Call(self, node: ast.Call):
        # Closure arguments are added after this optimization pass, so a call
        # may read the name even when it is not explicit in the source AST.
        self.used = True


def _continuation_uses(name: str, body: typing.Iterable[ast.stmt]) -> bool:
    collector = _ContinuationUseCollector(name)
    for statement in body:
        collector.visit(statement)
    return collector.used


def _positively_validated_names(node: ast.AST) -> typing.Set[str]:
    """Names whose Data constructor is checked on every true path."""

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and getattr(node.func, "orig_id", None) == "~bool"
    ):
        return _positively_validated_names(node.args[0])
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and getattr(node.func, "orig_id", None) == "isinstance"
        and isinstance(node.args[0], ast.Name)
    ):
        return {node.args[0].id}
    if isinstance(node, ast.BoolOp):
        validated = [_positively_validated_names(value) for value in node.values]
        if isinstance(node.op, ast.And):
            return set().union(*validated)
        if isinstance(node.op, ast.Or) and validated:
            return set.intersection(*validated)
    return set()


class _EffectBeforeReadDetector:
    """Detect calls evaluated before the first read of a name."""

    def __init__(self, name: str):
        self.name = name
        self.effect_seen = False
        self.read_seen = False
        self.unsafe = False

    def visit(self, node: ast.AST) -> None:
        if self.read_seen:
            return
        if (
            isinstance(node, ast.Name)
            and node.id == self.name
            and isinstance(node.ctx, ast.Load)
        ):
            self.unsafe = self.effect_seen
            self.read_seen = True
            return
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            return
        if isinstance(node, ast.Call):
            for child in ast.iter_child_nodes(node):
                self.visit(child)
                if self.read_seen:
                    return
            self.effect_seen = True
            return
        for child in ast.iter_child_nodes(node):
            self.visit(child)
            if self.read_seen:
                return


def _effect_precedes_first_read(node: ast.AST, name: str) -> bool:
    detector = _EffectBeforeReadDetector(name)
    detector.visit(node)
    return detector.unsafe


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
    branch. A fallthrough region converts the value back to its data-backed type
    only when its continuation may still read it.

    Expected read counts assume equally likely ``if`` branches and one loop
    iteration unless source comments provide ``branch-probability`` or
    ``iterations`` hints.
    """

    step = "Caching repeatedly used narrowed values"

    def __init__(self, allow_isinstance_anything: bool = False):
        self.allow_isinstance_anything = allow_isinstance_anything
        self.continuations: typing.List[typing.List[ast.stmt]] = []

    def visit_sequence(self, body: typing.List[ast.stmt]) -> typing.List[ast.stmt]:
        rewritten = []
        live_body = [node for node in body if node is not None]
        for index, node in enumerate(live_body):
            self.continuations.append(live_body[index + 1 :])
            try:
                updated = self.visit(node)
            finally:
                self.continuations.pop()
            if updated is None:
                continue
            rewritten.append(updated)
        return rewritten

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
        positively_validated: typing.Set[str],
        loop_reentry: bool = False,
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
            conversion_safe = name in positively_validated or template.integrity_checked
            if not conversion_safe:
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
            live_after = loop_reentry or (
                can_fall_through
                and any(
                    _continuation_uses(name, continuation)
                    for continuation in self.continuations
                )
            )
            threshold = thresholds[1 if live_after else 0]
            if accesses.unsafe or expected_reads < threshold:
                continue
            selected[name] = (template, source_typ, target_typ)

        if not selected:
            return self.visit_sequence(list(body))

        rewritten = list(body)
        for name, (template, source_typ, target_typ) in selected.items():
            live_after = loop_reentry or (
                can_fall_through
                and any(
                    _continuation_uses(name, continuation)
                    for continuation in self.continuations
                )
            )
            rewritten = self._rewrite_candidate_regions(
                rewritten,
                name,
                template,
                source_typ,
                target_typ,
                live_after,
                name in positively_validated or template.integrity_checked,
            )
        return self.visit_sequence(rewritten)

    def _rewrite_candidate_regions(
        self,
        body: typing.List[ast.stmt],
        name: str,
        template: ast.Name,
        source_typ: Type,
        target_typ: InstanceType,
        live_after: bool,
        conversion_safe: bool,
    ) -> typing.List[ast.stmt]:
        """Cache a representation at the first read on each profitable path."""

        counter = _ExpectedReadCounter(name)
        thresholds = next(
            limits
            for kind, limits in READ_THRESHOLDS.items()
            if isinstance(target_typ.typ, kind)
        )
        rewritten: typing.List[ast.stmt] = []
        for index, statement in enumerate(body):
            remainder = list(body[index + 1 :])
            remainder_uses = _continuation_uses(name, remainder) or live_after
            if (
                isinstance(statement, ast.If)
                and counter.expression(statement.test) == 0
            ):
                nested = copy(statement)
                nested.body = self._rewrite_candidate_regions(
                    list(statement.body),
                    name,
                    template,
                    source_typ,
                    target_typ,
                    remainder_uses,
                    conversion_safe,
                )
                nested.orelse = self._rewrite_candidate_regions(
                    list(statement.orelse),
                    name,
                    template,
                    source_typ,
                    target_typ,
                    remainder_uses,
                    conversion_safe,
                )
                rewritten.append(nested)
                continue
            if (
                isinstance(statement, (ast.For, ast.While))
                and not conversion_safe
                and (
                    counter.expression(
                        statement.iter
                        if isinstance(statement, ast.For)
                        else statement.test
                    )
                    == 0
                )
            ):
                nested = copy(statement)
                nested.body = self._rewrite_candidate_regions(
                    list(statement.body),
                    name,
                    template,
                    source_typ,
                    target_typ,
                    True,
                    conversion_safe,
                )
                nested.orelse = self._rewrite_candidate_regions(
                    list(statement.orelse),
                    name,
                    template,
                    source_typ,
                    target_typ,
                    remainder_uses,
                    conversion_safe,
                )
                rewritten.append(nested)
                continue
            if isinstance(statement, (ast.FunctionDef, ast.ClassDef)):
                rewritten.append(statement)
                continue
            if counter.expression(statement) == 0:
                rewritten.append(statement)
                continue
            if _effect_precedes_first_read(statement, name):
                rewritten.append(statement)
                continue

            region = list(body[index:])
            expected_reads, _ = counter.sequence(region)
            region_falls_through = all(
                getattr(region_statement, "can_fall_through", True)
                for region_statement in region
            )
            restore = region_falls_through and live_after
            threshold = thresholds[1 if restore else 0]
            if expected_reads < threshold:
                rewritten.extend(region)
                return rewritten
            representations = {name: target_typ}
            narrowed = _RepresentationRewriter(representations).visit_sequence(region)
            prefix = [
                _assignment(template, target_typ, DataInstanceType(target_typ.typ))
            ]
            suffix = [_assignment(template, source_typ, target_typ)] if restore else []
            return rewritten + prefix + narrowed + suffix
        return rewritten

    def _visit_conditional(self, node):
        rewritten = copy(node)
        rewritten.test = self.visit(node.test)
        typechecks, inverse_typechecks = TypeCheckVisitor(
            self.allow_isinstance_anything
        ).visit(rewritten.test)
        names = _TestNameCollector()
        names.visit(rewritten.test)
        positively_validated = _positively_validated_names(rewritten.test)
        rewritten.body = self._rewrite_arm(
            list(node.body),
            typechecks,
            names.names,
            getattr(node, "body_can_fall_through", True),
            positively_validated,
            isinstance(node, ast.While),
        )
        rewritten.orelse = self._rewrite_arm(
            list(node.orelse),
            inverse_typechecks,
            names.names,
            getattr(node, "orelse_can_fall_through", True),
            set(),
        )
        return rewritten

    def visit_If(self, node: ast.If):
        return self._visit_conditional(node)

    def visit_While(self, node: ast.While):
        return self._visit_conditional(node)
