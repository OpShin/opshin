import ast
from copy import deepcopy

from ..contract_interface import CONTRACT_METHOD_SPECS
from ..util import CompilingNodeTransformer, custom_fix_missing_locations


class _RewriteContractSelfReferences(ast.NodeTransformer):
    def __init__(self, field_name_map, helper_function_names, local_name_map):
        self.field_parameter_names = tuple(field_name_map.values())
        self.field_name_map = dict(field_name_map)
        self.helper_function_names = dict(helper_function_names)
        self.local_name_map = dict(local_name_map)

    def visit_Attribute(self, node: ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            assert isinstance(
                node.ctx, ast.Load
            ), "Contract fields are immutable and may not be assigned through self."
            if node.attr in self.field_name_map:
                return ast.copy_location(
                    ast.Name(id=self.field_name_map[node.attr], ctx=ast.Load()),
                    node,
                )
            if node.attr in self.helper_function_names:
                return ast.copy_location(
                    ast.Name(id=self.helper_function_names[node.attr], ctx=ast.Load()),
                    node,
                )
            assert False, f"Contract has no field or method named '{node.attr}'."
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id not in self.local_name_map:
            return node
        return ast.copy_location(
            ast.Name(id=self.local_name_map[node.id], ctx=node.ctx),
            node,
        )

    def visit_Call(self, node: ast.Call):
        node = self.generic_visit(node)
        if not isinstance(node.func, ast.Name):
            return node
        if node.func.id not in self.helper_function_names.values():
            return node
        return ast.copy_location(
            ast.Call(
                func=node.func,
                args=[
                    ast.Name(id=field_name, ctx=ast.Load())
                    for field_name in self.field_parameter_names
                ]
                + node.args,
                keywords=node.keywords,
            ),
            node,
        )


class RewriteContractMethods(CompilingNodeTransformer):
    step = "Rewriting Contract entrypoints"
    _internal_name_prefix = "__contract+"

    def visit_Module(self, node: ast.Module) -> ast.Module:
        node = self.generic_visit(node)
        has_validator = any(
            isinstance(statement, ast.FunctionDef) and statement.name == "validator"
            for statement in node.body
        )
        if has_validator:
            return node
        contract_class = next(
            (
                statement
                for statement in node.body
                if isinstance(statement, ast.ClassDef) and statement.name == "Contract"
            ),
            None,
        )
        if contract_class is None:
            return node
        contract_methods = {
            statement.name: statement
            for statement in contract_class.body
            if isinstance(statement, ast.FunctionDef)
        }
        supported_methods = [
            contract_method
            for contract_method in CONTRACT_METHOD_SPECS
            if contract_method.method_name in contract_methods
        ]
        if not supported_methods:
            return node
        self._check_contract_class(contract_class, supported_methods, contract_methods)
        field_annotations = self._field_annotations(contract_class)
        module_names = self._module_bound_names(node)
        generated_names = set(module_names)
        field_parameter_names = self._field_parameter_names(
            field_annotations, generated_names
        )
        helper_function_names = self._helper_function_names(
            contract_methods, generated_names
        )
        method_argument_name_maps = self._method_argument_name_maps(
            contract_methods, generated_names
        )
        supported_method_names = {
            supported_method.method_name for supported_method in supported_methods
        }
        referenced_methods = self._self_method_references(contract_methods.values())
        lifted_methods = [
            self._lift_contract_method(
                method,
                field_annotations,
                field_parameter_names,
                helper_function_names,
                method_argument_name_maps[method.name],
            )
            for method in contract_methods.values()
            if method.name not in supported_method_names
            or method.name in referenced_methods
        ]
        rewritten_entrypoint_bodies = {
            supported_method.method_name: self._rewrite_method_body(
                contract_methods[supported_method.method_name],
                field_parameter_names,
                helper_function_names,
                method_argument_name_maps[supported_method.method_name],
            )
            for supported_method in supported_methods
        }
        context_argument_name = self._make_reserved_name("context", generated_names)
        generated_names.add(context_argument_name)
        return_annotation = deepcopy(
            contract_methods[supported_methods[0].method_name].returns
        )
        for supported_method in supported_methods[1:]:
            candidate = contract_methods[supported_method.method_name].returns
            assert ast.dump(candidate) == ast.dump(
                return_annotation
            ), "All Contract entrypoint methods must have the same return annotation."
        validator_function = ast.FunctionDef(
            name="validator",
            args=ast.arguments(
                posonlyargs=[],
                args=[
                    ast.arg(
                        arg=field_parameter_names[field_name],
                        annotation=deepcopy(annotation),
                    )
                    for field_name, annotation in field_annotations
                ]
                + [
                    ast.arg(
                        arg=context_argument_name,
                        annotation=ast.Name(id="ScriptContext", ctx=ast.Load()),
                    )
                ],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=self._validator_body(
                field_parameter_names,
                supported_methods,
                contract_methods,
                method_argument_name_maps,
                rewritten_entrypoint_bodies,
                context_argument_name,
            ),
            decorator_list=[],
            returns=return_annotation,
            type_comment=None,
        )
        validator_function = custom_fix_missing_locations(
            ast.copy_location(validator_function, contract_class), contract_class
        )
        rewritten_body = []
        for statement in node.body:
            if statement is contract_class:
                rewritten_body.extend(lifted_methods)
                rewritten_body.append(validator_function)
            else:
                rewritten_body.append(statement)
        node.body = rewritten_body
        return node

    def _module_bound_names(self, node: ast.Module):
        bound_names = set()
        for statement in node.body:
            if isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                bound_names.add(statement.name)
            elif isinstance(statement, ast.Import):
                for alias in statement.names:
                    bound_names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(statement, ast.ImportFrom):
                for alias in statement.names:
                    bound_names.add(alias.asname or alias.name)
            elif isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        bound_names.add(target.id)
            elif isinstance(statement, ast.AnnAssign) and isinstance(
                statement.target, ast.Name
            ):
                bound_names.add(statement.target.id)
        return bound_names

    def _check_contract_class(
        self, contract_class, supported_methods, contract_methods
    ):
        if any(
            contract_method.method_name == "raw"
            for contract_method in supported_methods
        ):
            assert (
                len(supported_methods) == 1
            ), "Contract may define either raw or purpose-specific entrypoints, not both."
        for supported_method in supported_methods:
            self._check_method_signature(
                contract_methods[supported_method.method_name], supported_method
            )
        spending_method_names = {"spend", "spend_with_datum"}
        assert (
            len(
                [
                    supported_method
                    for supported_method in supported_methods
                    if supported_method.method_name in spending_method_names
                ]
            )
            <= 1
        ), "Contract may define at most one spending entrypoint: spend or spend_with_datum."
        assert not any(
            (
                isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.target.id == "CONSTR_ID"
            )
            or (
                isinstance(statement, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "CONSTR_ID"
                    for target in statement.targets
                )
            )
            for statement in contract_class.body
        ), "Contract classes must not define CONSTR_ID."
        assert not any(
            isinstance(statement, ast.Assign)
            and any(isinstance(target, ast.Name) for target in statement.targets)
            for statement in contract_class.body
        ), "Contract fields must be annotated; unannotated Contract fields are not supported."

    def _field_annotations(self, contract_class):
        field_annotations = []
        for statement in contract_class.body:
            if not isinstance(statement, ast.AnnAssign):
                continue
            assert isinstance(
                statement.target, ast.Name
            ), "Contract fields must be named attributes."
            field_annotations.append(
                (statement.target.id, deepcopy(statement.annotation))
            )
        return field_annotations

    def _field_parameter_names(self, field_annotations, used_names):
        field_parameter_names = {}
        for field_name, _ in field_annotations:
            internal_name = self._make_reserved_name(f"field_{field_name}", used_names)
            field_parameter_names[field_name] = internal_name
            used_names.add(internal_name)
        return field_parameter_names

    def _helper_function_names(self, contract_methods, used_names):
        helper_function_names = {}
        for method_name in contract_methods:
            helper_function_name = self._make_reserved_name(
                f"method_{method_name}", used_names
            )
            helper_function_names[method_name] = helper_function_name
            used_names.add(helper_function_name)
        return helper_function_names

    def _method_argument_name_maps(self, contract_methods, used_names):
        method_argument_name_maps = {}
        for method_name, method in contract_methods.items():
            argument_name_map = {}
            for argument in method.args.args[1:]:
                internal_name = self._make_reserved_name(
                    f"arg_{method_name}_{argument.arg}", used_names
                )
                argument_name_map[argument.arg] = internal_name
                used_names.add(internal_name)
            method_argument_name_maps[method_name] = argument_name_map
        return method_argument_name_maps

    def _self_method_references(self, methods):
        referenced_methods = set()
        for method in methods:
            for node in ast.walk(method):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute):
                    continue
                if not (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                ):
                    continue
                referenced_methods.add(node.func.attr)
        return referenced_methods

    def _rewrite_method_body(
        self,
        method,
        field_parameter_names,
        helper_function_names,
        argument_name_map,
    ):
        body_rewriter = _RewriteContractSelfReferences(
            field_parameter_names, helper_function_names, argument_name_map
        )
        return [body_rewriter.visit(deepcopy(statement)) for statement in method.body]

    def _lift_contract_method(
        self,
        method: ast.FunctionDef,
        field_annotations,
        field_parameter_names,
        helper_function_names,
        argument_name_map,
    ) -> ast.FunctionDef:
        assert not method.decorator_list, "Contract methods must not have decorators."
        assert (
            not method.args.posonlyargs
            and not method.args.vararg
            and not method.args.kwonlyargs
            and not method.args.kwarg
            and not method.args.defaults
            and not method.args.kw_defaults
        ), "Contract methods must use plain positional parameters without defaults."
        lifted_method = ast.FunctionDef(
            name=helper_function_names[method.name],
            args=ast.arguments(
                posonlyargs=[],
                args=[
                    ast.arg(
                        arg=field_parameter_names[field_name],
                        annotation=deepcopy(annotation),
                    )
                    for field_name, annotation in field_annotations
                ]
                + [
                    ast.arg(
                        arg=argument_name_map[argument.arg],
                        annotation=deepcopy(argument.annotation),
                    )
                    for argument in method.args.args[1:]
                ],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=self._rewrite_method_body(
                method,
                field_parameter_names,
                helper_function_names,
                argument_name_map,
            ),
            decorator_list=[],
            returns=deepcopy(method.returns),
            type_comment=method.type_comment,
        )
        return custom_fix_missing_locations(
            ast.copy_location(lifted_method, method), method
        )

    def _make_reserved_name(self, preferred_name: str, used_names):
        reserved_name = f"{self._internal_name_prefix}{preferred_name}"
        if reserved_name not in used_names:
            return reserved_name
        suffix = 0
        while f"{reserved_name}_{suffix}" in used_names:
            suffix += 1
        return f"{reserved_name}_{suffix}"

    def _check_method_signature(self, method: ast.FunctionDef, supported_method):
        assert (
            not method.args.posonlyargs
            and not method.args.vararg
            and not method.args.kwonlyargs
            and not method.args.kwarg
            and not method.args.defaults
            and not method.args.kw_defaults
        ), f"Contract method '{method.name}' must use plain positional parameters without defaults."
        actual_arguments = tuple(argument.arg for argument in method.args.args)
        assert (
            actual_arguments
        ), f"Contract method '{method.name}' must accept self as first parameter."
        assert (
            actual_arguments[0] == "self"
        ), f"Contract method '{method.name}' must accept self as first parameter."
        expected_argument_count = supported_method.onchain_argument_count + 1
        assert len(actual_arguments) == expected_argument_count, (
            f"Contract method '{method.name}' must accept self plus "
            f"{supported_method.onchain_argument_count} on-chain parameters."
        )
        context_annotation = method.args.args[-1].annotation
        if context_annotation is not None:
            assert (
                isinstance(context_annotation, ast.Name)
                and context_annotation.id == "ScriptContext"
            ), f"Contract method '{method.name}' must annotate context as ScriptContext."

    def _annotation_union_members(self, annotation):
        if isinstance(annotation, ast.Name) and annotation.id == "OutputDatum":
            return [annotation]
        if (
            isinstance(annotation, ast.Subscript)
            and isinstance(annotation.value, ast.Name)
            and annotation.value.id == "Union"
        ):
            if isinstance(annotation.slice, ast.Tuple):
                return list(annotation.slice.elts)
            return [annotation.slice]
        return [annotation]

    def _datum_loading_strategy(self, annotation):
        if isinstance(annotation, ast.Name) and annotation.id == "OutputDatum":
            return "attachment"
        union_members = self._annotation_union_members(annotation)
        if len(union_members) == 1 and union_members[0] is annotation:
            return "unsafe_raw"
        member_names = {
            member.id for member in union_members if isinstance(member, ast.Name)
        }
        if "NoOutputDatum" not in member_names:
            return "unsafe_raw"
        attachment_names = {"NoOutputDatum", "SomeOutputDatum", "SomeOutputDatumHash"}
        if len(member_names) == len(union_members) and member_names.issubset(
            attachment_names
        ):
            return "attachment"
        return "optional_raw"

    def _annotation_without_member(self, annotation, member_name):
        union_members = self._annotation_union_members(annotation)
        remaining_members = [
            deepcopy(member)
            for member in union_members
            if not (isinstance(member, ast.Name) and member.id == member_name)
        ]
        if len(remaining_members) == len(union_members):
            return deepcopy(annotation)
        assert remaining_members, "Expected at least one remaining union member."
        if len(remaining_members) == 1:
            return remaining_members[0]
        if (
            isinstance(annotation, ast.Subscript)
            and isinstance(annotation.value, ast.Name)
            and annotation.value.id == "Union"
        ):
            return ast.Subscript(
                value=ast.Name(id="Union", ctx=ast.Load()),
                slice=ast.Tuple(elts=remaining_members, ctx=ast.Load()),
                ctx=ast.Load(),
            )
        assert False, "Contract datum unions must use typing.Union syntax."

    def _validator_body(
        self,
        field_parameter_names,
        supported_methods,
        contract_methods,
        method_argument_name_maps,
        rewritten_entrypoint_bodies,
        context_argument_name,
    ):
        used_names = set(field_parameter_names.values()) | {context_argument_name}
        body = []
        if supported_methods[0].method_name == "raw":
            context_name = method_argument_name_maps["raw"][
                contract_methods["raw"].args.args[1].arg
            ]
            if context_name != context_argument_name:
                body.append(
                    ast.Assign(
                        targets=[ast.Name(id=context_name, ctx=ast.Store())],
                        value=ast.Name(id=context_argument_name, ctx=ast.Load()),
                    )
                )
            body.extend(deepcopy(rewritten_entrypoint_bodies["raw"]))
            return body
        purpose_name = self._make_reserved_name("purpose", used_names)
        used_names.add(purpose_name)
        body.append(
            ast.Assign(
                targets=[ast.Name(id=purpose_name, ctx=ast.Store())],
                value=ast.Attribute(
                    value=ast.Name(id=context_argument_name, ctx=ast.Load()),
                    attr="purpose",
                    ctx=ast.Load(),
                ),
            )
        )
        current_branch = None
        for index, supported_method in enumerate(supported_methods):
            method = contract_methods[supported_method.method_name]
            method_argument_names = [argument.arg for argument in method.args.args[1:]]
            branch_names = method_argument_name_maps[supported_method.method_name]
            branch_used_names = set(used_names) | set(branch_names.values())
            branch_body = []
            context_name = branch_names[method_argument_names[-1]]
            if context_name != context_argument_name:
                branch_body.append(
                    ast.Assign(
                        targets=[ast.Name(id=context_name, ctx=ast.Store())],
                        value=ast.Name(id=context_argument_name, ctx=ast.Load()),
                    )
                )
            if supported_method.method_name == "spend_with_datum":
                datum_argument_name = method_argument_names[0]
                redeemer_argument_name = method_argument_names[1]
                datum_name = branch_names[datum_argument_name]
                redeemer_name = branch_names[redeemer_argument_name]
                datum_annotation = deepcopy(method.args.args[1].annotation)
                redeemer_annotation = deepcopy(method.args.args[2].annotation)
                datum_loading_strategy = self._datum_loading_strategy(datum_annotation)
                resolved_datum_name = self._make_reserved_name(
                    "datum", branch_used_names
                )
                branch_used_names.add(resolved_datum_name)
                branch_body.append(
                    ast.AnnAssign(
                        target=ast.Name(id=redeemer_name, ctx=ast.Store()),
                        annotation=redeemer_annotation,
                        value=ast.Attribute(
                            value=ast.Name(id=context_name, ctx=ast.Load()),
                            attr="redeemer",
                            ctx=ast.Load(),
                        ),
                        simple=1,
                    )
                )
                if datum_loading_strategy == "attachment":
                    branch_body.append(
                        ast.AnnAssign(
                            target=ast.Name(id=resolved_datum_name, ctx=ast.Store()),
                            annotation=ast.Name(id="OutputDatum", ctx=ast.Load()),
                            value=ast.Call(
                                func=ast.Name(id="own_datum", ctx=ast.Load()),
                                args=[ast.Name(id=context_name, ctx=ast.Load())],
                                keywords=[],
                            ),
                            simple=1,
                        )
                    )
                    branch_body.append(
                        ast.AnnAssign(
                            target=ast.Name(id=datum_name, ctx=ast.Store()),
                            annotation=datum_annotation,
                            value=ast.Name(id=resolved_datum_name, ctx=ast.Load()),
                            simple=1,
                        )
                    )
                elif datum_loading_strategy == "optional_raw":
                    unwrapped_datum_name = self._make_reserved_name(
                        "unwrapped_datum", branch_used_names
                    )
                    raw_datum_annotation = self._annotation_without_member(
                        datum_annotation, "NoOutputDatum"
                    )
                    branch_body.append(
                        ast.AnnAssign(
                            target=ast.Name(id=resolved_datum_name, ctx=ast.Store()),
                            annotation=ast.Name(id="OutputDatum", ctx=ast.Load()),
                            value=ast.Call(
                                func=ast.Name(id="own_datum", ctx=ast.Load()),
                                args=[ast.Name(id=context_name, ctx=ast.Load())],
                                keywords=[],
                            ),
                            simple=1,
                        )
                    )
                    branch_body.append(
                        ast.If(
                            test=ast.Call(
                                func=ast.Name(id="isinstance", ctx=ast.Load()),
                                args=[
                                    ast.Name(id=resolved_datum_name, ctx=ast.Load()),
                                    ast.Name(id="SomeOutputDatum", ctx=ast.Load()),
                                ],
                                keywords=[],
                            ),
                            body=[
                                ast.AnnAssign(
                                    target=ast.Name(
                                        id=unwrapped_datum_name, ctx=ast.Store()
                                    ),
                                    annotation=raw_datum_annotation,
                                    value=ast.Attribute(
                                        value=ast.Name(
                                            id=resolved_datum_name, ctx=ast.Load()
                                        ),
                                        attr="datum",
                                        ctx=ast.Load(),
                                    ),
                                    simple=1,
                                ),
                                ast.AnnAssign(
                                    target=ast.Name(id=datum_name, ctx=ast.Store()),
                                    annotation=deepcopy(datum_annotation),
                                    value=ast.Name(
                                        id=unwrapped_datum_name, ctx=ast.Load()
                                    ),
                                    simple=1,
                                ),
                            ]
                            + deepcopy(
                                rewritten_entrypoint_bodies[
                                    supported_method.method_name
                                ]
                            ),
                            orelse=[
                                ast.Assert(
                                    test=ast.Call(
                                        func=ast.Name(id="isinstance", ctx=ast.Load()),
                                        args=[
                                            ast.Name(
                                                id=resolved_datum_name,
                                                ctx=ast.Load(),
                                            ),
                                            ast.Name(
                                                id="NoOutputDatum",
                                                ctx=ast.Load(),
                                            ),
                                        ],
                                        keywords=[],
                                    ),
                                    msg=None,
                                ),
                                ast.AnnAssign(
                                    target=ast.Name(id=datum_name, ctx=ast.Store()),
                                    annotation=deepcopy(datum_annotation),
                                    value=ast.Name(
                                        id=resolved_datum_name, ctx=ast.Load()
                                    ),
                                    simple=1,
                                ),
                            ],
                        )
                    )
                    branch_body[-1].orelse.extend(
                        deepcopy(
                            rewritten_entrypoint_bodies[supported_method.method_name]
                        )
                    )
                else:
                    branch_body.append(
                        ast.AnnAssign(
                            target=ast.Name(id=datum_name, ctx=ast.Store()),
                            annotation=datum_annotation,
                            value=ast.Call(
                                func=ast.Name(id="own_datum_unsafe", ctx=ast.Load()),
                                args=[ast.Name(id=context_name, ctx=ast.Load())],
                                keywords=[],
                            ),
                            simple=1,
                        )
                    )
                if datum_loading_strategy != "optional_raw":
                    branch_body.extend(
                        deepcopy(
                            rewritten_entrypoint_bodies[supported_method.method_name]
                        )
                    )
            else:
                redeemer_argument_name = method_argument_names[0]
                redeemer_name = branch_names[redeemer_argument_name]
                redeemer_annotation = deepcopy(method.args.args[1].annotation)
                branch_body.extend(
                    [
                        ast.AnnAssign(
                            target=ast.Name(id=redeemer_name, ctx=ast.Store()),
                            annotation=redeemer_annotation,
                            value=ast.Attribute(
                                value=ast.Name(id=context_name, ctx=ast.Load()),
                                attr="redeemer",
                                ctx=ast.Load(),
                            ),
                            simple=1,
                        ),
                    ]
                    + deepcopy(
                        rewritten_entrypoint_bodies[supported_method.method_name]
                    )
                )
            branch = ast.If(
                test=ast.Call(
                    func=ast.Name(id="isinstance", ctx=ast.Load()),
                    args=[
                        ast.Name(id=purpose_name, ctx=ast.Load()),
                        ast.Name(
                            id=supported_method.purpose_class.__name__, ctx=ast.Load()
                        ),
                    ],
                    keywords=[],
                ),
                body=branch_body,
                orelse=[],
            )
            if index == 0:
                body.append(branch)
                current_branch = branch
            else:
                current_branch.orelse = [branch]
                current_branch = branch
        current_branch.orelse = [
            ast.Assert(
                test=ast.Constant(value=False),
                msg=ast.Constant(value="Unsupported script purpose for Contract"),
            )
        ]
        return body
