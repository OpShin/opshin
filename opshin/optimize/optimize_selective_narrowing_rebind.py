from ast import AST, ClassDef, FunctionDef, Load, Name, Store, While, If
from contextlib import nullcontext
from copy import copy
from functools import partial
from functools import lru_cache
import typing

from ..typed_ast import TypedAssign, TypedName
from ..typed_util import ScopedSequenceNodeTransformer
from ..type_impls import (
    AnyType,
    ByteStringType,
    DataInstanceType,
    DictType,
    InstanceType,
    IntegerType,
    ListType,
    Type,
    UnionType,
    strip_data_instance_type,
)
from ..type_inference import TypeCheckVisitor, map_to_orig_name

# Recompute these choices with:
# `uv run python scripts/recompute_selective_rebind_thresholds.py`
# If the optimizer choice tests fail, rerun that script and update this file.
LIST_REBIND_READ_THRESHOLD = 3
INTEGER_REBIND_READ_THRESHOLD = 6
BYTESTRING_REBIND_READ_THRESHOLD = 6


def is_kind(target_typ: InstanceType, kind: str) -> bool:
    if kind == "list":
        return isinstance(target_typ.typ, ListType)
    if kind == "dict":
        return isinstance(target_typ.typ, DictType)
    if kind == "int":
        return isinstance(target_typ.typ, IntegerType)
    if kind == "bytes":
        return isinstance(target_typ.typ, ByteStringType)
    raise AssertionError(f"Unknown kind {kind}")


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
        if (
            isinstance(node.func, Name)
            and getattr(node.func, "orig_id", None) == "isinstance"
        ):
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
        if (
            isinstance(node.func, Name)
            and getattr(node.func, "orig_id", None) == "isinstance"
        ):
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
        if (
            isinstance(node.func, Name)
            and getattr(node.func, "orig_id", None) == "isinstance"
        ):
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
        id=target_name,
        orig_id=map_to_orig_name(target_name),
        ctx=Store(),
        typ=target_typ,
    )
    value = TypedName(
        id=source_name,
        orig_id=map_to_orig_name(source_name),
        ctx=Load(),
        typ=source_typ,
    )
    assign = TypedAssign(targets=[target], value=value)
    return assign


class OptimizeSelectiveNarrowingRebind(ScopedSequenceNodeTransformer):
    step = "Selectively lowering repeated narrowed reads"

    def __init__(
        self,
        allow_isinstance_anything=False,
        forced_kind: typing.Optional[str] = None,
    ):
        self.allow_isinstance_anything = allow_isinstance_anything
        self.forced_kind = forced_kind
        self._temp_id = 0

    def fresh_temp_name(self, source_name: str) -> str:
        name = f"__narrowed_{source_name}_{self._temp_id}"
        self._temp_id += 1
        return name

    def eligible_rebinds(
        self, typchecks: typing.Dict[str, Type], test_name_types: typing.Dict[str, Type]
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
            target_typ = (
                narrowed
                if isinstance(narrowed, InstanceType)
                else InstanceType(narrowed)
            )
            target_typ = strip_data_instance_type(target_typ)
            if isinstance(target_typ.typ, (AnyType, UnionType)):
                continue
            if self.forced_kind is not None:
                if not is_kind(target_typ, self.forced_kind):
                    continue
            elif not isinstance(
                target_typ.typ, (ListType, IntegerType, ByteStringType)
            ):
                continue
            rebinds[name] = (DataInstanceType(target_typ.typ), target_typ)
        return rebinds

    def read_threshold(self, target_typ: InstanceType) -> typing.Optional[int]:
        if self.forced_kind is not None:
            return 0 if is_kind(target_typ, self.forced_kind) else None
        if isinstance(target_typ.typ, ListType):
            return LIST_REBIND_READ_THRESHOLD
        if isinstance(target_typ.typ, IntegerType):
            return INTEGER_REBIND_READ_THRESHOLD
        if isinstance(target_typ.typ, ByteStringType):
            return BYTESTRING_REBIND_READ_THRESHOLD
        return None

    @staticmethod
    def access_events(node_seq: typing.List[AST], name: str) -> typing.List[str]:
        collector = _AccessEventCollector(name)
        for stmt in node_seq:
            collector.visit(stmt)
        return collector.events

    def should_lower(self, target_typ: InstanceType, events: typing.List[str]) -> bool:
        reads = events.count("read")
        threshold = self.read_threshold(target_typ)
        if threshold is None or reads < threshold:
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
            if not self.should_lower(rebind[1], events):
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
        retyped_seq = _NameLoadRewriter(temp_replacements).visit_sequence(
            list(node_seq)
        )
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


def eval_with_mode(
    source_code: str,
    *args,
    mode: str,
    forced_kind: typing.Optional[str] = None,
):
    from unittest.mock import patch

    from .. import builder
    from ..util import NoOp

    builder._static_compile.cache_clear()
    context = nullcontext()
    if mode == "noop":
        context = patch("opshin.compiler.OptimizeSelectiveNarrowingRebind", NoOp)
    elif mode == "forced":
        context = patch(
            "opshin.compiler.OptimizeSelectiveNarrowingRebind",
            partial(OptimizeSelectiveNarrowingRebind, forced_kind=forced_kind),
        )
    with context:
        return builder.uplc_eval(builder._compile(source_code, *args))


def list_source(reads: int) -> str:
    expr = " + ".join(["len(v)"] * reads)
    return f"""
from typing import List, Union
from pycardano import Datum as Anything, PlutusData

def validator(v: Union[int, List[Anything]], n: int) -> int:
    if isinstance(v, List):
        return {expr}
    return 0
"""


def int_source(reads: int) -> str:
    expr = " + ".join(["v"] * reads)
    return f"""
from typing import Union

def validator(v: Union[int, bytes]) -> int:
    if isinstance(v, int):
        return {expr}
    return 0
"""


def bytes_source(reads: int) -> str:
    expr = " + ".join(["len(v)"] * reads)
    return f"""
from typing import Union

def validator(v: Union[int, bytes]) -> int:
    if isinstance(v, bytes):
        return {expr}
    return 0
"""


def dict_source(reads: int) -> str:
    expr = " + ".join(["len(v)"] * reads)
    return f"""
from typing import Dict, Union
from pycardano import Datum as Anything, PlutusData

def validator(v: Union[int, Dict[Anything, Anything]], n: int) -> int:
    if isinstance(v, Dict):
        return {expr}
    return 0
"""


@lru_cache(maxsize=None)
def forced_beats_noop(kind: str, reads: int) -> bool:
    if kind == "list":
        source_code = list_source(reads)
        args = ([1, 2, 3], 0)
    elif kind == "int":
        source_code = int_source(reads)
        args = (5,)
    elif kind == "bytes":
        source_code = bytes_source(reads)
        args = (b"abcde",)
    elif kind == "dict":
        source_code = dict_source(reads)
        args = ({1: 2, 3: 4}, 0)
    else:
        raise AssertionError(f"Unknown kind {kind}")
    noop_eval = eval_with_mode(source_code, *args, mode="noop")
    forced_eval = eval_with_mode(source_code, *args, mode="forced", forced_kind=kind)
    return (
        forced_eval.cost.cpu <= noop_eval.cost.cpu
        and forced_eval.cost.memory <= noop_eval.cost.memory
    )
