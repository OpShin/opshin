import ast
from copy import deepcopy

from ..contract_interface import CONTRACT_METHOD_SPECS
from ..util import CompilingNodeTransformer


class RewriteContractMethods(CompilingNodeTransformer):
    step = "Rewriting Contract entrypoints"

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
        field_annotations = []
        for statement in contract_class.body:
            if not isinstance(statement, ast.AnnAssign):
                continue
            assert isinstance(
                statement.target, ast.Name
            ), "Contract fields must be named attributes."
            if statement.target.id == "CONSTR_ID":
                continue
            field_annotations.append(
                (statement.target.id, deepcopy(statement.annotation))
            )
        context_argument_name = self._make_unique_name(
            contract_methods[supported_methods[0].method_name].args.args[-1].arg,
            {field_name for field_name, _ in field_annotations},
        )
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
                    ast.arg(arg=field_name, annotation=annotation)
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
                field_annotations,
                supported_methods,
                contract_methods,
                context_argument_name,
            ),
            decorator_list=[],
            returns=return_annotation,
            type_comment=None,
        )
        validator_function = ast.copy_location(validator_function, contract_class)
        node.body.append(validator_function)
        return node

    def _make_unique_name(self, preferred_name: str, used_names):
        if preferred_name not in used_names:
            return preferred_name
        suffix = 0
        while f"{preferred_name}_{suffix}" in used_names:
            suffix += 1
        return f"{preferred_name}_{suffix}"

    def _check_method_signature(self, method: ast.FunctionDef, supported_method):
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
        if (
            isinstance(annotation, ast.Subscript)
            and isinstance(annotation.value, ast.Name)
            and annotation.value.id == "Union"
        ):
            if isinstance(annotation.slice, ast.Tuple):
                return list(annotation.slice.elts)
            return [annotation.slice]
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            return self._annotation_union_members(
                annotation.left
            ) + self._annotation_union_members(annotation.right)
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
        result = remaining_members[0]
        for member in remaining_members[1:]:
            result = ast.BinOp(left=result, op=ast.BitOr(), right=member)
        return result

    def _resolve_spent_output_assignment(self, target_name, context_name, purpose_name):
        return ast.Assign(
            targets=[ast.Name(id=target_name, ctx=ast.Store())],
            value=ast.Subscript(
                value=ast.ListComp(
                    elt=ast.Attribute(
                        value=ast.Name(id="tx_input", ctx=ast.Load()),
                        attr="resolved",
                        ctx=ast.Load(),
                    ),
                    generators=[
                        ast.comprehension(
                            target=ast.Name(id="tx_input", ctx=ast.Store()),
                            iter=ast.Attribute(
                                value=ast.Attribute(
                                    value=ast.Name(id=context_name, ctx=ast.Load()),
                                    attr="transaction",
                                    ctx=ast.Load(),
                                ),
                                attr="inputs",
                                ctx=ast.Load(),
                            ),
                            ifs=[
                                ast.Compare(
                                    left=ast.Attribute(
                                        value=ast.Name(id="tx_input", ctx=ast.Load()),
                                        attr="out_ref",
                                        ctx=ast.Load(),
                                    ),
                                    ops=[ast.Eq()],
                                    comparators=[
                                        ast.Attribute(
                                            value=ast.Name(
                                                id=purpose_name, ctx=ast.Load()
                                            ),
                                            attr="tx_out_ref",
                                            ctx=ast.Load(),
                                        )
                                    ],
                                )
                            ],
                            is_async=0,
                        )
                    ],
                ),
                slice=ast.Constant(value=0),
                ctx=ast.Load(),
            ),
        )

    def _resolve_attached_datum_statements(
        self,
        attached_datum_name,
        resolved_datum_name,
        spent_output_name,
        context_name,
    ):
        return [
            ast.AnnAssign(
                target=ast.Name(id=attached_datum_name, ctx=ast.Store()),
                annotation=ast.Name(id="OutputDatum", ctx=ast.Load()),
                value=ast.Attribute(
                    value=ast.Name(id=spent_output_name, ctx=ast.Load()),
                    attr="datum",
                    ctx=ast.Load(),
                ),
                simple=1,
            ),
            ast.If(
                test=ast.Call(
                    func=ast.Name(id="isinstance", ctx=ast.Load()),
                    args=[
                        ast.Name(id=attached_datum_name, ctx=ast.Load()),
                        ast.Name(id="SomeOutputDatumHash", ctx=ast.Load()),
                    ],
                    keywords=[],
                ),
                body=[
                    ast.AnnAssign(
                        target=ast.Name(id=resolved_datum_name, ctx=ast.Store()),
                        annotation=ast.Name(id="OutputDatum", ctx=ast.Load()),
                        value=ast.Call(
                            func=ast.Name(id="SomeOutputDatum", ctx=ast.Load()),
                            args=[
                                ast.Subscript(
                                    value=ast.Attribute(
                                        value=ast.Attribute(
                                            value=ast.Name(
                                                id=context_name, ctx=ast.Load()
                                            ),
                                            attr="transaction",
                                            ctx=ast.Load(),
                                        ),
                                        attr="datums",
                                        ctx=ast.Load(),
                                    ),
                                    slice=ast.Attribute(
                                        value=ast.Name(
                                            id=attached_datum_name, ctx=ast.Load()
                                        ),
                                        attr="datum_hash",
                                        ctx=ast.Load(),
                                    ),
                                    ctx=ast.Load(),
                                )
                            ],
                            keywords=[],
                        ),
                        simple=1,
                    )
                ],
                orelse=[
                    ast.AnnAssign(
                        target=ast.Name(id=resolved_datum_name, ctx=ast.Store()),
                        annotation=ast.Name(id="OutputDatum", ctx=ast.Load()),
                        value=ast.Name(id=attached_datum_name, ctx=ast.Load()),
                        simple=1,
                    )
                ],
            ),
        ]

    def _validator_body(
        self,
        field_annotations,
        supported_methods,
        contract_methods,
        context_argument_name,
    ):
        used_names = {field_name for field_name, _ in field_annotations}
        used_names.add(context_argument_name)
        contract_name = self._make_unique_name("contract", used_names)
        used_names.add(contract_name)
        purpose_name = self._make_unique_name("purpose", used_names)
        used_names.add(purpose_name)
        body = [
            ast.Assign(
                targets=[ast.Name(id=contract_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="Contract", ctx=ast.Load()),
                    args=[
                        ast.Name(id=field_name, ctx=ast.Load())
                        for field_name, _ in field_annotations
                    ],
                    keywords=[],
                ),
            ),
            ast.Assign(
                targets=[ast.Name(id=purpose_name, ctx=ast.Store())],
                value=ast.Attribute(
                    value=ast.Name(id=context_argument_name, ctx=ast.Load()),
                    attr="purpose",
                    ctx=ast.Load(),
                ),
            ),
        ]
        if supported_methods[0].method_name == "raw":
            method = contract_methods["raw"]
            context_name = method.args.args[1].arg
            if context_name != context_argument_name:
                body.append(
                    ast.Assign(
                        targets=[ast.Name(id=context_name, ctx=ast.Store())],
                        value=ast.Name(id=context_argument_name, ctx=ast.Load()),
                    )
                )
            body.append(
                ast.Return(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=contract_name, ctx=ast.Load()),
                            attr="raw",
                            ctx=ast.Load(),
                        ),
                        args=[ast.Name(id=context_name, ctx=ast.Load())],
                        keywords=[],
                    )
                )
            )
            return body
        for index, supported_method in enumerate(supported_methods):
            method = contract_methods[supported_method.method_name]
            method_argument_names = [argument.arg for argument in method.args.args[1:]]
            branch_names = {}
            branch_used_names = set(used_names)
            for argument_name in method_argument_names:
                unique_argument_name = self._make_unique_name(
                    argument_name, branch_used_names
                )
                branch_names[argument_name] = unique_argument_name
                branch_used_names.add(unique_argument_name)
            branch_body = []
            context_name = branch_names[method_argument_names[-1]]
            if context_name != context_argument_name:
                branch_body.append(
                    ast.Assign(
                        targets=[ast.Name(id=context_name, ctx=ast.Store())],
                        value=ast.Name(id=context_argument_name, ctx=ast.Load()),
                    )
                )
            if supported_method.method_name == "spend":
                datum_argument_name = method_argument_names[0]
                redeemer_argument_name = method_argument_names[1]
                datum_name = branch_names[datum_argument_name]
                redeemer_name = branch_names[redeemer_argument_name]
                datum_annotation = deepcopy(method.args.args[1].annotation)
                redeemer_annotation = deepcopy(method.args.args[2].annotation)
                datum_loading_strategy = self._datum_loading_strategy(datum_annotation)
                spent_output_name = self._make_unique_name(
                    "spent_output", branch_used_names
                )
                branch_used_names.add(spent_output_name)
                attached_datum_name = self._make_unique_name(
                    "attached_datum", branch_used_names
                )
                branch_used_names.add(attached_datum_name)
                resolved_datum_name = self._make_unique_name(
                    "resolved_datum", branch_used_names
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
                branch_body.append(
                    self._resolve_spent_output_assignment(
                        spent_output_name, context_name, purpose_name
                    )
                )
                branch_body.extend(
                    self._resolve_attached_datum_statements(
                        attached_datum_name,
                        resolved_datum_name,
                        spent_output_name,
                        context_name,
                    )
                )
                if datum_loading_strategy == "attachment":
                    branch_body.append(
                        ast.AnnAssign(
                            target=ast.Name(id=datum_name, ctx=ast.Store()),
                            annotation=datum_annotation,
                            value=ast.Name(id=resolved_datum_name, ctx=ast.Load()),
                            simple=1,
                        )
                    )
                elif datum_loading_strategy == "optional_raw":
                    unwrapped_datum_name = self._make_unique_name(
                        "unwrapped_datum", branch_used_names
                    )
                    branch_used_names.add(unwrapped_datum_name)
                    raw_datum_annotation = self._annotation_without_member(
                        datum_annotation, "NoOutputDatum"
                    )
                    branch_body.extend(
                        [
                            ast.If(
                                test=ast.Call(
                                    func=ast.Name(id="isinstance", ctx=ast.Load()),
                                    args=[
                                        ast.Name(
                                            id=resolved_datum_name, ctx=ast.Load()
                                        ),
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
                                                id=resolved_datum_name,
                                                ctx=ast.Load(),
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
                                    ast.Return(
                                        value=ast.Call(
                                            func=ast.Attribute(
                                                value=ast.Name(
                                                    id=contract_name, ctx=ast.Load()
                                                ),
                                                attr=supported_method.method_name,
                                                ctx=ast.Load(),
                                            ),
                                            args=[
                                                ast.Name(id=datum_name, ctx=ast.Load()),
                                                ast.Name(
                                                    id=redeemer_name, ctx=ast.Load()
                                                ),
                                                ast.Name(
                                                    id=context_name, ctx=ast.Load()
                                                ),
                                            ],
                                            keywords=[],
                                        )
                                    ),
                                ],
                                orelse=[
                                    ast.Assert(
                                        test=ast.Call(
                                            func=ast.Name(
                                                id="isinstance", ctx=ast.Load()
                                            ),
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
                                    ast.Return(
                                        value=ast.Call(
                                            func=ast.Attribute(
                                                value=ast.Name(
                                                    id=contract_name, ctx=ast.Load()
                                                ),
                                                attr=supported_method.method_name,
                                                ctx=ast.Load(),
                                            ),
                                            args=[
                                                ast.Name(id=datum_name, ctx=ast.Load()),
                                                ast.Name(
                                                    id=redeemer_name, ctx=ast.Load()
                                                ),
                                                ast.Name(
                                                    id=context_name, ctx=ast.Load()
                                                ),
                                            ],
                                            keywords=[],
                                        )
                                    ),
                                ],
                            ),
                        ]
                    )
                else:
                    branch_body.append(
                        ast.Assert(
                            test=ast.Call(
                                func=ast.Name(id="isinstance", ctx=ast.Load()),
                                args=[
                                    ast.Name(id=resolved_datum_name, ctx=ast.Load()),
                                    ast.Name(id="SomeOutputDatum", ctx=ast.Load()),
                                ],
                                keywords=[],
                            ),
                            msg=ast.Constant(
                                value="No datum was attached to the UTxO being spent by this Contract."
                            ),
                        )
                    )
                    branch_body.append(
                        ast.AnnAssign(
                            target=ast.Name(id=datum_name, ctx=ast.Store()),
                            annotation=datum_annotation,
                            value=ast.Attribute(
                                value=ast.Name(id=resolved_datum_name, ctx=ast.Load()),
                                attr="datum",
                                ctx=ast.Load(),
                            ),
                            simple=1,
                        )
                    )
                if datum_loading_strategy != "optional_raw":
                    branch_body.append(
                        ast.Return(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id=contract_name, ctx=ast.Load()),
                                    attr=supported_method.method_name,
                                    ctx=ast.Load(),
                                ),
                                args=[
                                    ast.Name(id=datum_name, ctx=ast.Load()),
                                    ast.Name(id=redeemer_name, ctx=ast.Load()),
                                    ast.Name(id=context_name, ctx=ast.Load()),
                                ],
                                keywords=[],
                            )
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
                        ast.Return(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id=contract_name, ctx=ast.Load()),
                                    attr=supported_method.method_name,
                                    ctx=ast.Load(),
                                ),
                                args=[
                                    ast.Name(id=redeemer_name, ctx=ast.Load()),
                                    ast.Name(id=context_name, ctx=ast.Load()),
                                ],
                                keywords=[],
                            )
                        ),
                    ]
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
