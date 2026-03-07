import unittest
import os

from frozendict import frozendict
import uplc.ast as uplc_ast

from .uplc_patch import get_uplc_ast_repr_limit, set_uplc_ast_repr_limit


def nested_lambda(depth: int) -> uplc_ast.AST:
    term = uplc_ast.Variable("x")
    for i in range(depth):
        term = uplc_ast.BoundStateLambda(
            f"v{i}",
            uplc_ast.Apply(term, uplc_ast.BuiltinInteger(i)),
            frozendict(),
        )
    return term


class UplcPatchTest(unittest.TestCase):
    def test_typechecked_error_uses_capped_uplc_repr(self):
        previous = set_uplc_ast_repr_limit(160)
        try:
            checked = uplc_ast.typechecked(uplc_ast.BuiltinInteger)(lambda x: x)
            with self.assertRaises(AssertionError) as ctx:
                checked(nested_lambda(25))
            message = str(ctx.exception)
        finally:
            set_uplc_ast_repr_limit(previous)

        self.assertIn("Argument 0 has invalid type", message)
        self.assertIn("...", message)
        self.assertLess(len(message), 320)

    def test_repr_limit_can_be_changed(self):
        previous = set_uplc_ast_repr_limit(80)
        try:
            short_repr = repr(nested_lambda(10))
            set_uplc_ast_repr_limit(400)
            long_repr = repr(nested_lambda(10))
        finally:
            set_uplc_ast_repr_limit(previous)

        self.assertLessEqual(len(short_repr), 80)
        self.assertGreater(len(long_repr), len(short_repr))

    def test_test_profile_sets_uplc_repr_limit(self):
        raw = os.getenv("OPSHIN_TEST_UPLC_REPR_LIMIT", "1200")
        self.assertEqual(
            get_uplc_ast_repr_limit(),
            None if raw in ("", "none", "None") else int(raw),
        )
