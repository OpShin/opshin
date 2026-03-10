from ast import AST, ClassDef, FunctionDef, Load, Name, Store, While, If
from copy import copy
import typing

from ..typed_ast import TypedAssign, TypedName
from ..typed_util import ScopedSequenceNodeTransformer
from ..type_impls import (
    AnyType,
    DataInstanceType,
    InstanceType,
    ListType,
    Type,
    UnionType,
    strip_data_instance_type,
)
from ..type_inference import TypeCheckVisitor, map_to_orig_name


class TestNameTypeCollector(typing.Protocol):
    name_types: typing.Dict[str, Type]


class _TestNameTypeCollector:
    def __init__(self):
        self.name_types: typing.Dict[str, Type] = {}

    def visit(self, node):
        method = getattr(self, f"visit_{node.__class__.__name__}", self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        for field in getattr(node, "_fields", []):
            value = getattr(node, field, None)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        self.visit(item)
            elif isinstance(value, AST):
                self.visit(value)

    def visit_Name(self, node: Name):
        if hasattr(node, "typ") and node.id not in self.name_types:
            self.name_types[node.id] = node.typ


class _AccessEventCollector:
    def __init__(self, name: str):
        self.name = name
        self.events: typing.List[str] = []

    def visit(self, node):
        method = getattr(self, f"visit_{node.__class__.__name__}", self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        for field in getattr(node, "_fields", []):
            value = getattr(node, field, None)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        self.visit(item)
            elif isinstance(value, AST):
                self.visit(value)

    def visit_FunctionDef(self, node: FunctionDef):
        return node

    def visit_ClassDef(self, node: ClassDef):
        return node

    def visit_Call(self, node):
        if isinstance(node.func, Name) and getattr(node.func, "orig_id", None) == "isinstance":
            return node
        return self.generic_visit(node)

    def visit_Name(self, node: Name):
        if node.id != self.name:
            return
        if isinstance(node.ctx, Load):
            self.events.append("read")
        elif isinstance(node.ctx, Store):
            self.events.append("write")


class _NameTypeRewriter(ScopedSequenceNodeTransformer):
    def __init__(self, replacement_types: typing.Dict[str, Type]):
        self.replacement_types = replacement_types

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        return node

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        return node

    def visit_Call(self, node):
        if isinstance(node.func, Name) and getattr(node.func, "orig_id", None) == "isinstance":
            return node
        return self.generic_visit(node)

    def visit_Name(self, node: Name) -> Name:
        if node.id not in self.replacement_types or not hasattr(node, "typ"):
            return node
        node_cp = copy(node)
        node_cp.typ = self.replacement_types[node.id]
        return node_cp


class _NameLoadRewriter(ScopedSequenceNodeTransformer):
    def __init__(self, replacements: typing.Dict[str, typing.Tuple[str, Type]]):
        self.replacements = replacements

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        return node

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        return node

    def visit_Call(self, node):
        if isinstance(node.func, Name) and getattr(node.func, "orig_id", None) == "isinstance":
            return node
        return self.generic_visit(node)

    def visit_Name(self, node: Name) -> Name:
        if (
            node.id not in self.replacements
            or not hasattr(node, "typ")
            or not isinstance(node.ctx, Load)
        ):
            return node
        replacement_id, replacement_typ = self.replacements[node.id]
        node_cp = copy(node)
        node_cp.id = replacement_id
        node_cp.orig_id = replacement_id
        node_cp.typ = replacement_typ
        return node_cp


def make_typed_rebind_assignment(
    source_name: str, target_name: str, source_typ: Type, target_typ: Type
):
    target = TypedName(
        id=target_name, orig_id=map_to_orig_name(target_name), ctx=Store(), typ=target_typ
    )
    value = TypedName(
        id=source_name, orig_id=map_to_orig_name(source_name), ctx=Load(), typ=source_typ
    )
    assign = TypedAssign(targets=[target], value=value)
    return assign


class OptimizeSelectiveNarrowingRebind(ScopedSequenceNodeTransformer):
    step = "Selectively lowering repeated narrowed reads"

    def __init__(self, allow_isinstance_anything=False):
        self.allow_isinstance_anything = allow_isinstance_anything
        self._temp_id = 0

    def fresh_temp_name(self, source_name: str) -> str:
        name = f"__narrowed_{source_name}_{self._temp_id}"
        self._temp_id += 1
        return name

    @staticmethod
    def eligible_rebinds(
        typchecks: typing.Dict[str, Type], test_name_types: typing.Dict[str, Type]
    ) -> typing.Dict[str, typing.Tuple[Type, InstanceType]]:
        rebinds = {}
        for name, narrowed in typchecks.items():
            source_typ = test_name_types.get(name)
            if not (
                isinstance(source_typ, DataInstanceType)
                or (
                    isinstance(source_typ, InstanceType)
                    and isinstance(source_typ.typ, (AnyType, UnionType))
                )
            ):
                continue
            target_typ = narrowed if isinstance(narrowed, InstanceType) else InstanceType(narrowed)
            target_typ = strip_data_instance_type(target_typ)
            if isinstance(target_typ.typ, (AnyType, UnionType)):
                continue
            if not isinstance(target_typ.typ, ListType):
                continue
            rebinds[name] = (DataInstanceType(target_typ.typ), target_typ)
        return rebinds

    @staticmethod
    def access_events(node_seq: typing.List[AST], name: str) -> typing.List[str]:
        collector = _AccessEventCollector(name)
        for stmt in node_seq:
            collector.visit(stmt)
        return collector.events

    @staticmethod
    def should_lower(events: typing.List[str]) -> bool:
        reads = events.count("read")
        if reads < 2:
            return False
        return "write" not in events

    def optimize_sequence_under_typechecks(
        self,
        node_seq: typing.List[AST],
        typchecks: typing.Dict[str, Type],
        test_name_types: typing.Dict[str, Type],
        can_fall_through: bool,
    ) -> typing.List[AST]:
        rebinds = self.eligible_rebinds(typchecks, test_name_types)
        selected: typing.Dict[str, typing.Tuple[Type, InstanceType]] = {}
        for name, rebind in rebinds.items():
            events = self.access_events(node_seq, name)
            if not self.should_lower(events):
                continue
            selected[name] = rebind
        if not selected:
            return self.visit_sequence(list(node_seq))

        temp_replacements = {
            name: (self.fresh_temp_name(name), target_typ)
            for name, (_, target_typ) in selected.items()
        }
        prefixes = []
        for name, (source_typ, target_typ) in selected.items():
            temp_name, _ = temp_replacements[name]
            prefixes.append(
                make_typed_rebind_assignment(name, temp_name, source_typ, target_typ)
            )
        retyped_seq = _NameLoadRewriter(temp_replacements).visit_sequence(list(node_seq))
        return prefixes + self.visit_sequence(retyped_seq)

    def visit_If(self, node: If) -> If:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        typchecks, inv_typchecks = TypeCheckVisitor(
            self.allow_isinstance_anything
        ).visit(node_cp.test)
        collector = _TestNameTypeCollector()
        collector.visit(node_cp.test)
        node_cp.body = self.optimize_sequence_under_typechecks(
            list(node.body),
            typchecks,
            collector.name_types,
            getattr(node, "body_can_fall_through", True),
        )
        node_cp.orelse = self.optimize_sequence_under_typechecks(
            list(node.orelse),
            inv_typchecks,
            collector.name_types,
            getattr(node, "orelse_can_fall_through", True),
        )
        return node_cp

    def visit_While(self, node: While) -> While:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        typchecks, inv_typchecks = TypeCheckVisitor(
            self.allow_isinstance_anything
        ).visit(node_cp.test)
        collector = _TestNameTypeCollector()
        collector.visit(node_cp.test)
        node_cp.body = self.optimize_sequence_under_typechecks(
            list(node.body),
            typchecks,
            collector.name_types,
            getattr(node, "body_can_fall_through", True),
        )
        node_cp.orelse = self.optimize_sequence_under_typechecks(
            list(node.orelse),
            inv_typchecks,
            collector.name_types,
            getattr(node, "orelse_can_fall_through", True),
        )
        return node_cp
