import ast

from opshin.util import NameSupply


def test_name_supply_uses_purpose_and_avoids_collisions():
    existing_names = {"__opshin_tuple_0"}
    tree = ast.parse("\n".join(f"{name} = 0" for name in existing_names))
    tuple_names = NameSupply.from_tree(tree, "tuple")
    default_names = NameSupply.from_tree(tree, "default")

    generated_names = {tuple_names.fresh_name(), tuple_names.fresh_name()}
    assert generated_names.isdisjoint(existing_names)
    assert len(generated_names) == 2
    assert default_names.fresh_name() not in generated_names
