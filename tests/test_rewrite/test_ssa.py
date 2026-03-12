import ast

from opshin.rewrite.rewrite_annotate_fallthrough import RewriteAnnotateFallthrough
from opshin.rewrite.rewrite_orig_name import RewriteOrigName
from opshin.rewrite.rewrite_scoping import RewriteScoping
from opshin.rewrite.rewrite_ssa import RewriteSSA


def run_ssa(source_code: str) -> ast.Module:
    prog = ast.parse(source_code)
    prog = RewriteOrigName().visit(prog)
    prog = RewriteScoping().visit(prog)
    prog = RewriteAnnotateFallthrough().visit(prog)
    prog = RewriteSSA().visit(prog)
    prog = RewriteAnnotateFallthrough().visit(prog)
    return prog


def test_rebinding_gets_distinct_versions():
    prog = run_ssa(
        """
def validator(y: int) -> int:
    x = y
    x = x + 1
    return x
"""
    )

    validator = prog.body[0]
    first_assign, second_assign, ret = validator.body

    assert first_assign.targets[0].id.endswith("_v1")
    assert second_assign.targets[0].id.endswith("_v2")
    assert second_assign.value.left.id == first_assign.targets[0].id
    assert ret.value.id == second_assign.targets[0].id


def test_if_branches_join_to_shared_version():
    prog = run_ssa(
        """
def validator(a: int, b: int, c: bool) -> int:
    x = a
    if c:
        x = b
    else:
        x = a + b
    return x
"""
    )

    validator = prog.body[0]
    initial_assign, if_stmt, ret = validator.body
    body_assign, body_join = if_stmt.body
    else_assign, else_join = if_stmt.orelse

    assert body_assign.targets[0].id != else_assign.targets[0].id
    assert body_join.targets[0].id == else_join.targets[0].id
    assert body_join.targets[0].id != initial_assign.targets[0].id
    assert body_join.value.id == body_assign.targets[0].id
    assert else_join.value.id == else_assign.targets[0].id
    assert ret.value.id == body_join.targets[0].id


def test_loop_written_names_stay_pinned_to_single_state_version():
    prog = run_ssa(
        """
from typing import List

def validator(xs: List[int]) -> int:
    total = 0
    for x in xs:
        total = total + x
    return total
"""
    )

    validator = prog.body[1]
    initial_assign, total_loop_prelude, for_stmt, ret = validator.body

    assert initial_assign.targets[0].id.endswith("_v1")
    assert total_loop_prelude.targets[0].id.endswith("_v2")
    assert for_stmt.target.id.endswith("_v1")
    assert for_stmt.body[0].targets[0].id == total_loop_prelude.targets[0].id
    assert for_stmt.body[0].value.left.id == total_loop_prelude.targets[0].id
    assert for_stmt.body[0].value.right.id == for_stmt.target.id
    assert ret.value.id == total_loop_prelude.targets[0].id
