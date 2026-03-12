from ast import *
from copy import copy, deepcopy

from ..util import CompilingNodeVisitor, CompilingNodeTransformer
from ..type_inference import INITIAL_SCOPE
from .optimize_remove_deadvars import SafeOperationVisitor, NameLoadCollector
from .optimize_const_folding import DefinedTimesVisitor

"""
Inlines simple variable assignments into their usage sites.

x = z
y = x * 2

becomes:

y = z * 2

This is safe when:
1. x is assigned exactly once
2. x is read only once OR the expression is simple (constant, name)
3. The expression is side-effect free (as determined by SafeOperationVisitor)
"""


class AssignmentCollector(CompilingNodeVisitor):
    step = "Collecting variable assignments for inlining"

    def __init__(self):
        self.assignments = {}

    def visit_Assign(self, node: Assign):
        if len(node.targets) == 1 and isinstance(node.targets[0], Name):
            self.assignments[node.targets[0].id] = node.value

    def visit_ClassDef(self, node):
        # Don't descend into class definitions
        pass

    def visit_FunctionDef(self, node):
        # Visit body to find assignments inside functions
        for s in node.body:
            self.visit(s)


class NameSubstitutor(CompilingNodeTransformer):
    step = "Substituting inlined expressions"

    def __init__(self, substitutions):
        self.substitutions = substitutions
        self.changed = False

    def visit_Name(self, node: Name):
        if isinstance(node.ctx, Load) and node.id in self.substitutions:
            new_node = deepcopy(self.substitutions[node.id])
            copy_location(new_node, node)
            self.changed = True
            return new_node
        return node


class OptimizeInlineExpressions(CompilingNodeTransformer):
    step = "Inlining simple expressions"

    def visit_Module(self, node: Module):
        node_cp = copy(node)

        while True:
            # Count how many times each variable is defined
            def_counter = DefinedTimesVisitor()
            def_counter.visit(node_cp)

            # Count how many times each variable is loaded
            load_counter = NameLoadCollector()
            load_counter.visit(node_cp)

            # Collect assignments (var_name -> expression)
            assign_collector = AssignmentCollector()
            assign_collector.visit(node_cp)

            # Names guaranteed to exist for SafeOperationVisitor
            guaranteed_names = (
                list(INITIAL_SCOPE.keys())
                + ["isinstance", "Union", "Dict", "List"]
                + [v for v, c in def_counter.vars.items() if c <= 1]
            )

            inlineable = {}
            for var, expr in assign_collector.assignments.items():
                # Variable must be assigned exactly once
                if def_counter.vars.get(var, 0) != 1:
                    continue

                # Check if expression is "simple" (constant or single-def name)
                is_simple = isinstance(expr, Constant) or (
                    isinstance(expr, Name)
                    and isinstance(expr.ctx, Load)
                    and def_counter.vars.get(expr.id, 0) <= 1
                )

                # Variable must be read once or have a simple expression
                is_read_once = load_counter.loaded.get(var, 0) <= 1
                if not (is_read_once or is_simple):
                    continue

                # Expression must be side-effect free
                if not SafeOperationVisitor(guaranteed_names).visit(expr):
                    continue

                inlineable[var] = expr

            if not inlineable:
                break

            # Perform substitution
            substitutor = NameSubstitutor(inlineable)
            node_cp = substitutor.visit(node_cp)

            if not substitutor.changed:
                break

        return node_cp
