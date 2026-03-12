from ast import *
from copy import copy

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
3. One of these holds:
   a. The expression is side-effect free (as determined by SafeOperationVisitor)
   b. The expression is guaranteed to be executed at the inlined site
      (every code path leads through there)
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


class GuaranteedLoadCollector(CompilingNodeVisitor):
    """Collects variable loads that are guaranteed to execute.

    A load is guaranteed if it is at the top level of the scope,
    not inside any branch (if/while/for body/orelse).
    Only the tests of if/while and the iter of for are guaranteed.
    """

    step = "Collecting guaranteed variable loads"

    def __init__(self):
        self.guaranteed = set()

    def visit_Name(self, node: Name):
        if isinstance(node.ctx, Load):
            self.guaranteed.add(node.id)

    def visit_BoolOp(self, node: BoolOp):
        # Only the first operand is guaranteed; later ones may short-circuit.
        self.visit(node.values[0])

    def visit_Compare(self, node: Compare):
        # In a comparison chain, only the left side and first comparator are
        # guaranteed to execute. Later comparators depend on earlier results.
        self.visit(node.left)
        if node.comparators:
            self.visit(node.comparators[0])

    def visit_If(self, node: If):
        # Only the test is guaranteed to execute, branches are not
        self.visit(node.test)

    def visit_IfExp(self, node: IfExp):
        # Only the test is guaranteed, body/orelse are conditional
        self.visit(node.test)

    def visit_While(self, node: While):
        # Only the test is guaranteed to execute (evaluated before loop entry)
        self.visit(node.test)

    def visit_For(self, node: For):
        # The iterable is guaranteed to be evaluated
        self.visit(node.iter)

    def visit_FunctionDef(self, node):
        # Visit body to find guaranteed loads inside functions
        for s in node.body:
            self.visit(s)

    def visit_ClassDef(self, node):
        # Don't descend into class definitions
        pass


class NameSubstitutor(CompilingNodeTransformer):
    step = "Substituting inlined expressions"

    def __init__(self, substitutions, removable):
        self.substitutions = substitutions
        self.removable = removable
        self.changed = False

    def generic_visit(self, node):
        # Override to use setattr instead of in-place list modification,
        # since the typed AST may use frozenlist for some fields
        for field, old_value in iter_fields(node):
            if isinstance(old_value, list):
                new_values = []
                for old_node in old_value:
                    if isinstance(old_node, AST):
                        value = self.visit(old_node)
                        if value is None:
                            continue
                        elif not isinstance(value, AST):
                            new_values.extend(value)
                            continue
                    else:
                        value = old_node
                    new_values.append(value)
                setattr(node, field, new_values)
            elif isinstance(old_value, AST):
                new_value = self.visit(old_value)
                if new_value is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_value)
        return node

    def visit_Name(self, node: Name):
        if isinstance(node.ctx, Load) and node.id in self.substitutions:
            new_node = copy(self.substitutions[node.id])
            copy_location(new_node, node)
            self.changed = True
            return new_node
        return node

    def visit_Assign(self, node: Assign):
        # Remove assignments for inlined variables whose expressions
        # don't reference other inlineable variables (safe to remove now).
        # Assignments referencing other inlined vars are kept for the next
        # iteration so their expressions can be substituted first.
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], Name)
            and node.targets[0].id in self.removable
        ):
            self.changed = True
            return Pass()
        return self.generic_visit(node)


class ScopedAssignmentCollector(AssignmentCollector):
    def visit_FunctionDef(self, node):
        pass


class ScopedGuaranteedLoadCollector(GuaranteedLoadCollector):
    def visit_FunctionDef(self, node):
        pass


class ScopedNameLoadCollector(NameLoadCollector):
    def visit_FunctionDef(self, node):
        pass

    def visit_ClassDef(self, node):
        pass


class ScopedDefinedTimesVisitor(DefinedTimesVisitor):
    def visit_FunctionDef(self, node):
        pass

    def visit_ClassDef(self, node):
        self.vars[node.name] += 1


class ScopedNameSubstitutor(NameSubstitutor):
    def visit_FunctionDef(self, node):
        return node

    def visit_ClassDef(self, node):
        return node


class OptimizeInlineExpressions(CompilingNodeTransformer):
    step = "Inlining simple expressions"

    def _collect_captured_vars(self, statements):
        captured_vars = set()
        for statement in statements:
            for child in walk(statement):
                if isinstance(child, FunctionDef) and hasattr(child, "typ"):
                    try:
                        captured_vars.update(child.typ.typ.bound_vars.keys())
                    except AttributeError:
                        pass
        return captured_vars

    def _optimize_statements(
        self,
        statements,
        *,
        arg_names=(),
        assignment_collector_cls=AssignmentCollector,
        load_collector_cls=NameLoadCollector,
        def_counter_cls=DefinedTimesVisitor,
        guaranteed_load_collector_cls=GuaranteedLoadCollector,
        substitutor_cls=NameSubstitutor,
    ):
        statements_cp = list(statements)

        while True:
            # Count how many times each variable is defined
            def_counter = def_counter_cls()
            for statement in statements_cp:
                def_counter.visit(statement)
            for arg_name in arg_names:
                def_counter.vars[arg_name] += 2

            # Count how many times each variable is loaded
            load_counter = load_collector_cls()
            for statement in statements_cp:
                load_counter.visit(statement)

            # Collect assignments (var_name -> expression)
            assign_collector = assignment_collector_cls()
            for statement in statements_cp:
                assign_collector.visit(statement)

            captured_vars = self._collect_captured_vars(statements_cp)

            # Collect loads that are guaranteed to execute (not inside branches)
            guaranteed_load_collector = guaranteed_load_collector_cls()
            for statement in statements_cp:
                guaranteed_load_collector.visit(statement)
            guaranteed_loads = guaranteed_load_collector.guaranteed

            # Names guaranteed to exist for SafeOperationVisitor.
            guaranteed_names = (
                list(INITIAL_SCOPE.keys())
                + ["isinstance", "Union", "Dict", "List"]
                + [v for v, c in def_counter.vars.items() if c == 1]
                + list(arg_names)
            )

            inlineable = {}
            for var, expr in assign_collector.assignments.items():
                # Variable must be assigned exactly once
                if def_counter.vars.get(var, 0) != 1:
                    continue

                # Don't inline variables captured by function closures
                if var in captured_vars:
                    continue

                # Check if expression is "simple": constant, single-def name,
                # or function argument name
                is_simple = isinstance(expr, Constant) or (
                    isinstance(expr, Name)
                    and isinstance(expr.ctx, Load)
                    and (
                        def_counter.vars.get(expr.id, 0) == 1 or expr.id in arg_names
                    )
                )

                # Variable must be read once or have a simple expression
                is_read_once = load_counter.loaded.get(var, 0) <= 1
                if not (is_read_once or is_simple):
                    continue

                is_safe = SafeOperationVisitor(guaranteed_names).visit(expr)
                is_guaranteed = is_read_once and var in guaranteed_loads

                if not (is_safe or is_guaranteed):
                    continue

                inlineable[var] = expr

            if not inlineable:
                break

            referenced_by_inlineable = set()
            for _, expr in inlineable.items():
                for child in walk(expr):
                    if (
                        isinstance(child, Name)
                        and isinstance(child.ctx, Load)
                        and child.id in inlineable
                    ):
                        referenced_by_inlineable.add(child.id)

            removable = {
                v for v in inlineable if v not in referenced_by_inlineable
            }

            substitutor = substitutor_cls(inlineable, removable)
            statements_cp = [substitutor.visit(statement) for statement in statements_cp]

            if not substitutor.changed:
                break

        return statements_cp

    def visit_Module(self, node: Module):
        node_cp = copy(node)
        node_cp.body = [self.visit(statement) for statement in node_cp.body]
        node_cp.body = self._optimize_statements(node_cp.body)
        return node_cp

    def visit_FunctionDef(self, node: FunctionDef):
        node_cp = copy(node)
        node_cp.body = [self.visit(statement) for statement in node_cp.body]
        node_cp.body = self._optimize_statements(
            node_cp.body,
            arg_names=[arg.arg for arg in node_cp.args.args],
            assignment_collector_cls=ScopedAssignmentCollector,
            load_collector_cls=ScopedNameLoadCollector,
            def_counter_cls=ScopedDefinedTimesVisitor,
            guaranteed_load_collector_cls=ScopedGuaranteedLoadCollector,
            substitutor_cls=ScopedNameSubstitutor,
        )
        return node_cp
