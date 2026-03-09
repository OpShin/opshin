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

    def _validator_body(
        self,
        field_annotations,
        supported_methods,
        contract_methods,
        context_argument_name,
    ):
        body = []
        used_names = {field_name for field_name, _ in field_annotations}
        used_names.add(context_argument_name)
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
                branch_body.extend(
                    [
                        ast.AnnAssign(
                            target=ast.Name(id=datum_name, ctx=ast.Store()),
                            annotation=datum_annotation,
                            value=ast.Call(
                                func=ast.Name(id="own_datum_unsafe", ctx=ast.Load()),
                                args=[ast.Name(id=context_name, ctx=ast.Load())],
                                keywords=[],
                            ),
                            simple=1,
                        ),
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
                                    value=ast.Call(
                                        func=ast.Name(id="Contract", ctx=ast.Load()),
                                        args=[
                                            ast.Name(id=field_name, ctx=ast.Load())
                                            for field_name, _ in field_annotations
                                        ],
                                        keywords=[],
                                    ),
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
                        ),
                    ]
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
                                    value=ast.Call(
                                        func=ast.Name(id="Contract", ctx=ast.Load()),
                                        args=[
                                            ast.Name(id=field_name, ctx=ast.Load())
                                            for field_name, _ in field_annotations
                                        ],
                                        keywords=[],
                                    ),
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
                        ast.Attribute(
                            value=ast.Name(id=context_argument_name, ctx=ast.Load()),
                            attr="purpose",
                            ctx=ast.Load(),
                        ),
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
