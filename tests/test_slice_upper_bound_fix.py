"""
Test to verify that None upper bounds in slicing create RawPlutoExpr
instead of len() Call nodes.
"""

import ast
import unittest
from opshin.type_inference import AggressiveTypeInferencer
from opshin.typed_ast import RawPlutoExpr
from ast import Call


class TestSliceUpperBoundFix(unittest.TestCase):
    """Test that None upper bounds create RawPlutoExpr instead of len() calls"""

    def test_list_slice_none_upper_bound_creates_raw_pluto_expr(self):
        """Test that list[:]  creates RawPlutoExpr for upper bound"""
        source_code = '''
def test(x: list[int]) -> list[int]:
    return x[:]
'''
        tree = ast.parse(source_code)
        inferencer = AggressiveTypeInferencer()
        result = inferencer.visit(tree)
        
        # Navigate to the slice expression
        func_def = result.body[0]
        return_stmt = func_def.body[0]
        slice_expr = return_stmt.value
        upper_bound = slice_expr.slice.upper
        
        # Verify it's a RawPlutoExpr, not a Call to len
        self.assertIsInstance(upper_bound, RawPlutoExpr,
                             "Upper bound should be RawPlutoExpr")
        self.assertNotIsInstance(upper_bound, Call,
                                "Upper bound should not be a Call")

    def test_bytes_slice_none_upper_bound_creates_raw_pluto_expr(self):
        """Test that bytes[:] creates RawPlutoExpr for upper bound"""
        source_code = '''
def test(x: bytes) -> bytes:
    return x[:]
'''
        tree = ast.parse(source_code)
        inferencer = AggressiveTypeInferencer()
        result = inferencer.visit(tree)
        
        # Navigate to the slice expression
        func_def = result.body[0]
        return_stmt = func_def.body[0]
        slice_expr = return_stmt.value
        upper_bound = slice_expr.slice.upper
        
        # Verify it's a RawPlutoExpr, not a Call to len
        self.assertIsInstance(upper_bound, RawPlutoExpr,
                             "Upper bound should be RawPlutoExpr")
        self.assertNotIsInstance(upper_bound, Call,
                                "Upper bound should not be a Call")

    def test_list_slice_with_explicit_upper_bound_still_works(self):
        """Test that list[:n] still works normally"""
        source_code = '''
def test(x: list[int], n: int) -> list[int]:
    return x[:n]
'''
        tree = ast.parse(source_code)
        inferencer = AggressiveTypeInferencer()
        result = inferencer.visit(tree)
        
        # Navigate to the slice expression
        func_def = result.body[0]
        return_stmt = func_def.body[0]
        slice_expr = return_stmt.value
        upper_bound = slice_expr.slice.upper
        
        # Should still be processed normally (visited)
        self.assertIsNotNone(upper_bound)
        self.assertIsNotNone(upper_bound.typ)


if __name__ == "__main__":
    unittest.main()