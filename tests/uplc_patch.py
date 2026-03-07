import dataclasses
import os
from collections.abc import Mapping, Sequence
from typing import Optional

import uplc.ast as uplc_ast


_ELLIPSIS = "..."
_ENV_NAME = "OPSHIN_TEST_UPLC_REPR_LIMIT"
_PATCHED = False


def _parse_limit(raw: Optional[str]) -> Optional[int]:
    if raw in (None, "", "none", "None"):
        return None
    limit = int(raw)
    if limit <= 0:
        raise ValueError(f"{_ENV_NAME} must be a positive integer or 'None'")
    return limit


_UPLC_REPR_LIMIT = _parse_limit(os.getenv(_ENV_NAME, "1200"))


def get_uplc_ast_repr_limit() -> Optional[int]:
    return _UPLC_REPR_LIMIT


def set_uplc_ast_repr_limit(limit: Optional[int]) -> Optional[int]:
    global _UPLC_REPR_LIMIT
    if limit is not None and limit <= 0:
        raise ValueError("UPLC repr limit must be a positive integer or None")
    previous = _UPLC_REPR_LIMIT
    _UPLC_REPR_LIMIT = limit
    return previous


def _truncate_text(text: str, budget: Optional[int]) -> str:
    if budget is None or len(text) <= budget:
        return text
    if budget <= len(_ELLIPSIS):
        return _ELLIPSIS[:budget]
    return text[: budget - len(_ELLIPSIS)] + _ELLIPSIS


def _render_sequence(
    values: Sequence,
    opener: str,
    closer: str,
    budget: Optional[int],
    seen: set[int],
) -> str:
    container = opener + closer
    if budget is not None and budget <= len(container):
        return _truncate_text(container, budget)

    remaining = None if budget is None else budget - len(opener) - len(closer)
    parts = []
    for index, value in enumerate(values):
        if remaining is not None and remaining <= len(_ELLIPSIS):
            parts.append(_truncate_text(_ELLIPSIS, remaining))
            break
        sep = ", " if index else ""
        if remaining is not None and len(sep) >= remaining:
            parts.append(_truncate_text(sep + _ELLIPSIS, remaining))
            break
        item_budget = None if remaining is None else remaining - len(sep)
        rendered = _render_value(value, item_budget, seen)
        part = sep + rendered
        parts.append(part)
        if remaining is not None:
            remaining -= len(part)
            if remaining <= 0:
                break
    return opener + "".join(parts) + closer


def _render_mapping(
    values: Mapping,
    opener: str,
    closer: str,
    budget: Optional[int],
    seen: set[int],
) -> str:
    container = opener + closer
    if budget is not None and budget <= len(container):
        return _truncate_text(container, budget)

    remaining = None if budget is None else budget - len(opener) - len(closer)
    parts = []
    for index, (key, value) in enumerate(values.items()):
        if remaining is not None and remaining <= len(_ELLIPSIS):
            parts.append(_truncate_text(_ELLIPSIS, remaining))
            break
        sep = ", " if index else ""
        if remaining is not None and len(sep) >= remaining:
            parts.append(_truncate_text(sep + _ELLIPSIS, remaining))
            break
        pair_budget = None if remaining is None else remaining - len(sep)
        key_budget = None if pair_budget is None else max(pair_budget // 2, 1)
        rendered_key = _render_value(key, key_budget, seen)
        rendered_value = _render_value(
            value,
            (
                None
                if pair_budget is None
                else max(pair_budget - len(rendered_key) - 2, 1)
            ),
            seen,
        )
        part = _truncate_text(sep + rendered_key + ": " + rendered_value, remaining)
        parts.append(part)
        if remaining is not None:
            remaining -= len(part)
            if remaining <= 0:
                break
    return opener + "".join(parts) + closer


def _render_ast(node: uplc_ast.AST, budget: Optional[int], seen: set[int]) -> str:
    node_id = id(node)
    cls_name = type(node).__name__
    if node_id in seen:
        return _truncate_text(f"{cls_name}(...)", budget)
    if not dataclasses.is_dataclass(node):
        return _truncate_text(cls_name, budget)

    opener = f"{cls_name}("
    closer = ")"
    if budget is not None and budget <= len(opener) + len(closer):
        return _truncate_text(opener + closer, budget)

    seen.add(node_id)
    try:
        remaining = None if budget is None else budget - len(opener) - len(closer)
        parts = []
        for index, field in enumerate(dataclasses.fields(node)):
            if remaining is not None and remaining <= len(_ELLIPSIS):
                parts.append(_truncate_text(_ELLIPSIS, remaining))
                break
            sep = ", " if index else ""
            label = f"{sep}{field.name}="
            if remaining is not None and len(label) >= remaining:
                parts.append(_truncate_text(label + _ELLIPSIS, remaining))
                break
            value_budget = None if remaining is None else remaining - len(label)
            rendered = _render_value(getattr(node, field.name), value_budget, seen)
            part = label + rendered
            if remaining is not None:
                part = _truncate_text(part, remaining)
                remaining -= len(part)
            parts.append(part)
            if remaining == 0:
                break
        return opener + "".join(parts) + closer
    finally:
        seen.remove(node_id)


def _render_value(value, budget: Optional[int], seen: set[int]) -> str:
    if isinstance(value, uplc_ast.AST):
        return _render_ast(value, budget, seen)
    if isinstance(value, Mapping):
        return _render_mapping(value, "{", "}", budget, seen)
    if isinstance(value, tuple):
        closer = ",)" if len(value) == 1 else ")"
        return _render_sequence(value, "(", closer, budget, seen)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return _render_sequence(value, "[", "]", budget, seen)
    return _truncate_text(repr(value), budget)


def _bounded_uplc_repr(self) -> str:
    return _render_value(self, _UPLC_REPR_LIMIT, set())


def _iter_ast_classes():
    stack = [uplc_ast.AST]
    seen = set()
    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        yield cls
        stack.extend(cls.__subclasses__())


def patch_uplc_ast_reprs() -> None:
    global _PATCHED
    if _PATCHED:
        return
    for cls in _iter_ast_classes():
        cls.__repr__ = _bounded_uplc_repr
    _PATCHED = True
