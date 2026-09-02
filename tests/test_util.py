import ast

from opshin.util import NameSupply


def test_name_supply_uses_purpose_and_avoids_collisions():
    existing_name = NameSupply("tuple").fresh_name()
    tree = ast.Module(
        body=[
            ast.Assign(
                targets=[ast.Name(id=existing_name, ctx=ast.Store())],
                value=ast.Constant(0),
            )
        ],
        type_ignores=[],
    )
    tuple_names = NameSupply.from_tree(tree, "tuple")
    default_names = NameSupply.from_tree(tree, "default")

    generated_names = {tuple_names.fresh_name(), tuple_names.fresh_name()}
    assert existing_name not in generated_names
    assert len(generated_names) == 2
    assert default_names.fresh_name() not in generated_names
