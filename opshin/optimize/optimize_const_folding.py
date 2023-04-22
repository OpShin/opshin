from copy import copy

import typing

from ast import *


try:
    unparse
except NameError:
    from astunparse import unparse

from ..util import CompilingNodeTransformer

"""
Pre-evaluates constant statements
"""

ACCEPTED_ATOMIC_TYPES = [
    int,
    str,
    bytes,
    type(None),
    bool,
]


class AnnotateConstantFolding(CompilingNodeTransformer):
    """
    Annotates all values whether they are computable at compile time
    Compile time static values are annotated with the attribute const = True
    """

    step = "Constant annotator"

    # tracks constant variable names
    scopes = [list(globals().keys())]

    def is_constant(self, name: str):
        name = name
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

    def enter_scope(self):
        self.scopes.append([])

    def exit_scope(self):
        self.scopes.pop()

    def set_constant(self, name: str):
        self.scopes[-1].append(name)

    def visit_sequence(self, node_seq: typing.List[stmt]):
        return [self.visit(s) for s in node_seq]

    def visit_BinOp(self, node: BinOp):
        node_cp = copy(node)
        node_cp.left = self.visit(node.left)
        node_cp.right = self.visit(node.right)
        node_cp.const = node_cp.left.const and node_cp.right.const
        return node_cp

    def visit_BoolOp(self, node: BoolOp):
        node_cp = copy(node)
        node_cp.values = [self.visit(v) for v in node.values]
        node_cp.const = all(v.const for v in node_cp.values)
        return node_cp

    def visit_UnaryOp(self, node: UnaryOp):
        node_cp = copy(node)
        node_cp.operand = self.visit(node.operand)
        node_cp.const = node_cp.operand
        return node_cp

    def visit_Compare(self, node: Compare):
        node_cp = copy(node)
        node_cp.left = self.visit(node.left)
        node_cp.comparators = [self.visit(c) for c in node.comparators]
        node_cp.const = node_cp.left.const and all(v.const for v in node.comparators)
        return node_cp

    def visit_Constant(self, node: Constant):
        node_cp = copy(node)
        node_cp.const = True
        return node_cp

    def visit_NoneType(self, node: None):
        node = Constant(None)
        node.const = True
        return node

    def visit_Assign(self, node: Assign):
        node_cp = copy(node)
        node_cp.value = self.visit(node_cp.value)
        if node_cp.value.const:
            for t in node.targets:
                if isinstance(t, Name):
                    self.set_constant(t.id)
        return node_cp

    def visit_AnnAssign(self, node: AnnAssign):
        node_cp = copy(node)
        if not isinstance(node_cp.target, Name):
            return node
        node_cp.value = self.visit(node_cp.value)
        if node_cp.value.const:
            self.set_constant(node_cp.target.id)
        return node_cp

    def visit_Name(self, node: Name):
        # depending on load or store context, return the value of the variable or its name
        if not isinstance(node.ctx, Load):
            return node
        node_cp = copy(node)
        node_cp.const = self.is_constant(node.id)
        return node_cp

    def visit_Expr(self, node: Expr):
        node_cp = copy(node)
        node_cp.value = self.visit(node.value)
        node_cp.const = node_cp.value.const
        return node_cp

    def visit_Call(self, node: Call):
        node_cp = copy(node)
        node_cp.func = self.visit(node.func)
        node_cp.args = [self.visit(a) for a in node.args]
        node_cp.keywords = [self.visit(k) for k in node.keywords]
        node_cp.const = (
            node_cp.func.const
            and all(a.const for a in node_cp.args)
            and all(k.const for k in node.keywords)
        )
        return node_cp

    def visit_FunctionDef(self, node: FunctionDef):
        self.set_constant(node.name)
        self.enter_scope()
        node_cp = self.generic_visit(node)
        self.exit_scope()
        return node_cp

    def visit_While(self, node: While):
        cond = node.test
        compiled_s = []
        if node.orelse:
            # If there is orelse, transform it to an appended sequence (TODO check if this is correct)
            cn = copy(node)
            cn.orelse = []
            return self.visit_sequence([cn] + node.orelse)
        # return rf"(\{STATEMONAD} -> let g = (\s f -> if ({compiled_c} s) then f ({compiled_s} s) f else s) in (g {STATEMONAD} g))"
        return plt.Lambda(
            [STATEMONAD],
            plt.Let(
                bindings=[
                    (
                        "g",
                        plt.Lambda(
                            ["s", "f"],
                            plt.Ite(
                                plt.Apply(compiled_c, plt.Var("s")),
                                plt.Apply(
                                    plt.Var("f"),
                                    plt.Apply(compiled_s, plt.Var("s")),
                                    plt.Var("f"),
                                ),
                                plt.Var("s"),
                            ),
                        ),
                    ),
                ],
                term=plt.Apply(plt.Var("g"), plt.Var(STATEMONAD), plt.Var("g")),
            ),
        )

    def visit_For(self, node: TypedFor) -> plt.AST:
        if node.orelse:
            # If there is orelse, transform it to an appended sequence (TODO check if this is correct)
            cn = copy(node)
            cn.orelse = []
            return self.visit_sequence([cn] + node.orelse)
        assert isinstance(node.iter.typ, InstanceType)
        if isinstance(node.iter.typ.typ, ListType):
            assert isinstance(
                node.target, Name
            ), "Can only assign value to singleton element"
            return plt.Lambda(
                [STATEMONAD],
                plt.FoldList(
                    plt.Apply(self.visit(node.iter), plt.Var(STATEMONAD)),
                    plt.Lambda(
                        [STATEMONAD, "e"],
                        plt.Apply(
                            self.visit_sequence(node.body),
                            extend_statemonad(
                                [node.target.id],
                                [plt.Var("e")],
                                plt.Var(STATEMONAD),
                            ),
                        ),
                    ),
                    plt.Var(STATEMONAD),
                ),
            )
        raise NotImplementedError(
            "Compilation of for statements for anything but lists not implemented yet"
        )

    def visit_If(self, node: TypedIf) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            plt.Ite(
                plt.Apply(self.visit(node.test), plt.Var(STATEMONAD)),
                plt.Apply(self.visit_sequence(node.body), plt.Var(STATEMONAD)),
                plt.Apply(self.visit_sequence(node.orelse), plt.Var(STATEMONAD)),
            ),
        )

    def visit_Return(self, node: TypedReturn) -> plt.AST:
        raise NotImplementedError(
            "Compilation of return statements except for last statement in function is not supported."
        )

    def visit_Pass(self, node: TypedPass) -> plt.AST:
        return self.visit_sequence([])

    def visit_Subscript(self, node: TypedSubscript) -> plt.AST:
        assert isinstance(
            node.value.typ, InstanceType
        ), "Can only access elements of instances, not classes"
        if isinstance(node.value.typ.typ, TupleType):
            assert isinstance(
                node.slice, Constant
            ), "Only constant index access for tuples is supported"
            assert isinstance(
                node.slice.value, int
            ), "Only constant index integer access for tuples is supported"
            index = node.slice.value
            if index < 0:
                index += len(node.value.typ.typ.typs)
            assert isinstance(node.ctx, Load), "Tuples are read-only"
            return plt.Lambda(
                [STATEMONAD],
                plt.FunctionalTupleAccess(
                    plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                    index,
                    len(node.value.typ.typ.typs),
                ),
            )
        if isinstance(node.value.typ.typ, PairType):
            assert isinstance(
                node.slice, Constant
            ), "Only constant index access for pairs is supported"
            assert isinstance(
                node.slice.value, int
            ), "Only constant index integer access for pairs is supported"
            index = node.slice.value
            if index < 0:
                index += 2
            assert isinstance(node.ctx, Load), "Pairs are read-only"
            assert (
                0 <= index < 2
            ), f"Pairs only have 2 elements, index should be 0 or 1, is {node.slice.value}"
            member_func = plt.FstPair if index == 0 else plt.SndPair
            # the content of pairs is always Data, so we need to unwrap
            member_typ = node.typ
            return plt.Lambda(
                [STATEMONAD],
                transform_ext_params_map(member_typ)(
                    member_func(
                        plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                    ),
                ),
            )
        if isinstance(node.value.typ.typ, ListType):
            assert (
                node.slice.typ == IntegerInstanceType
            ), "Only single element list index access supported"
            return plt.Lambda(
                [STATEMONAD],
                plt.Let(
                    [
                        ("l", plt.Apply(self.visit(node.value), plt.Var(STATEMONAD))),
                        (
                            "raw_i",
                            plt.Apply(self.visit(node.slice), plt.Var(STATEMONAD)),
                        ),
                        (
                            "i",
                            plt.Ite(
                                plt.LessThanInteger(plt.Var("raw_i"), plt.Integer(0)),
                                plt.AddInteger(
                                    plt.Var("raw_i"), plt.LengthList(plt.Var("l"))
                                ),
                                plt.Var("raw_i"),
                            ),
                        ),
                    ],
                    plt.IndexAccessList(plt.Var("l"), plt.Var("i")),
                ),
            )
        elif isinstance(node.value.typ.typ, DictType):
            dict_typ = node.value.typ.typ
            if not isinstance(node.slice, Slice):
                return plt.Lambda(
                    [STATEMONAD],
                    plt.Let(
                        [
                            (
                                "key",
                                plt.Apply(self.visit(node.slice), plt.Var(STATEMONAD)),
                            )
                        ],
                        transform_ext_params_map(dict_typ.value_typ)(
                            plt.SndPair(
                                plt.FindList(
                                    plt.Apply(
                                        self.visit(node.value), plt.Var(STATEMONAD)
                                    ),
                                    plt.Lambda(
                                        ["x"],
                                        plt.EqualsData(
                                            transform_output_map(dict_typ.key_typ)(
                                                plt.Var("key")
                                            ),
                                            plt.FstPair(plt.Var("x")),
                                        ),
                                    ),
                                    plt.TraceError("KeyError"),
                                ),
                            ),
                        ),
                    ),
                )
        elif isinstance(node.value.typ.typ, ByteStringType):
            if not isinstance(node.slice, Slice):
                return plt.Lambda(
                    [STATEMONAD],
                    plt.Let(
                        [
                            (
                                "bs",
                                plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                            ),
                            (
                                "raw_ix",
                                plt.Apply(self.visit(node.slice), plt.Var(STATEMONAD)),
                            ),
                            (
                                "ix",
                                plt.Ite(
                                    plt.LessThanInteger(
                                        plt.Var("raw_ix"), plt.Integer(0)
                                    ),
                                    plt.AddInteger(
                                        plt.Var("raw_ix"),
                                        plt.LengthOfByteString(plt.Var("bs")),
                                    ),
                                    plt.Var("raw_ix"),
                                ),
                            ),
                        ],
                        plt.IndexByteString(plt.Var("bs"), plt.Var("ix")),
                    ),
                )
            elif isinstance(node.slice, Slice):
                return plt.Lambda(
                    [STATEMONAD],
                    plt.Let(
                        [
                            (
                                "bs",
                                plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                            ),
                            (
                                "raw_i",
                                plt.Apply(
                                    self.visit(node.slice.lower), plt.Var(STATEMONAD)
                                ),
                            ),
                            (
                                "i",
                                plt.Ite(
                                    plt.LessThanInteger(
                                        plt.Var("raw_i"), plt.Integer(0)
                                    ),
                                    plt.AddInteger(
                                        plt.Var("raw_i"),
                                        plt.LengthOfByteString(plt.Var("bs")),
                                    ),
                                    plt.Var("raw_i"),
                                ),
                            ),
                            (
                                "raw_j",
                                plt.Apply(
                                    self.visit(node.slice.upper), plt.Var(STATEMONAD)
                                ),
                            ),
                            (
                                "j",
                                plt.Ite(
                                    plt.LessThanInteger(
                                        plt.Var("raw_j"), plt.Integer(0)
                                    ),
                                    plt.AddInteger(
                                        plt.Var("raw_j"),
                                        plt.LengthOfByteString(plt.Var("bs")),
                                    ),
                                    plt.Var("raw_j"),
                                ),
                            ),
                            (
                                "drop",
                                plt.Ite(
                                    plt.LessThanEqualsInteger(
                                        plt.Var("i"), plt.Integer(0)
                                    ),
                                    plt.Integer(0),
                                    plt.Var("i"),
                                ),
                            ),
                            (
                                "take",
                                plt.SubtractInteger(plt.Var("j"), plt.Var("drop")),
                            ),
                        ],
                        plt.Ite(
                            plt.LessThanEqualsInteger(plt.Var("j"), plt.Var("i")),
                            plt.ByteString(b""),
                            plt.SliceByteString(
                                plt.Var("drop"),
                                plt.Var("take"),
                                plt.Var("bs"),
                            ),
                        ),
                    ),
                )
        raise NotImplementedError(
            f'Could not implement subscript "{node.slice}" of "{node.value}"'
        )

    def visit_Tuple(self, node: TypedTuple) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            plt.FunctionalTuple(
                *(plt.Apply(self.visit(e), plt.Var(STATEMONAD)) for e in node.elts)
            ),
        )

    def visit_ClassDef(self, node: TypedClassDef) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            extend_statemonad(
                [node.name],
                [node.class_typ.constr()],
                plt.Var(STATEMONAD),
            ),
        )

    def visit_Attribute(self, node: TypedAttribute) -> plt.AST:
        assert isinstance(
            node.typ, InstanceType
        ), "Can only access attributes of instances"
        obj = self.visit(node.value)
        attr = node.value.typ.attribute(node.attr)
        return plt.Lambda(
            [STATEMONAD], plt.Apply(attr, plt.Apply(obj, plt.Var(STATEMONAD)))
        )

    def visit_Assert(self, node: TypedAssert) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            plt.Ite(
                plt.Apply(self.visit(node.test), plt.Var(STATEMONAD)),
                plt.Var(STATEMONAD),
                plt.Apply(
                    plt.Error(),
                    plt.Trace(
                        plt.Apply(self.visit(node.msg), plt.Var(STATEMONAD)), plt.Unit()
                    )
                    if node.msg is not None
                    else plt.Unit(),
                ),
            ),
        )

    def visit_RawPlutoExpr(self, node: RawPlutoExpr) -> plt.AST:
        return node.expr

    def visit_List(self, node: TypedList) -> plt.AST:
        assert isinstance(node.typ, InstanceType)
        assert isinstance(node.typ.typ, ListType)
        l = empty_list(node.typ.typ.typ)
        for e in reversed(node.elts):
            l = plt.MkCons(plt.Apply(self.visit(e), plt.Var(STATEMONAD)), l)
        return plt.Lambda([STATEMONAD], l)

    def visit_Dict(self, node: TypedDict) -> plt.AST:
        assert isinstance(node.typ, InstanceType)
        assert isinstance(node.typ.typ, DictType)
        key_type = node.typ.typ.key_typ
        value_type = node.typ.typ.value_typ
        l = plt.EmptyDataPairList()
        for k, v in zip(node.keys, node.values):
            l = plt.MkCons(
                plt.MkPairData(
                    transform_output_map(key_type)(
                        plt.Apply(self.visit(k), plt.Var(STATEMONAD))
                    ),
                    transform_output_map(value_type)(
                        plt.Apply(self.visit(v), plt.Var(STATEMONAD))
                    ),
                ),
                l,
            )
        return plt.Lambda([STATEMONAD], l)

    def visit_IfExp(self, node: TypedIfExp) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            plt.Ite(
                plt.Apply(self.visit(node.test), plt.Var(STATEMONAD)),
                plt.Apply(self.visit(node.body), plt.Var(STATEMONAD)),
                plt.Apply(self.visit(node.orelse), plt.Var(STATEMONAD)),
            ),
        )

    def visit_ListComp(self, node: TypedListComp) -> plt.AST:
        assert len(node.generators) == 1, "Currently only one generator supported"
        gen = node.generators[0]
        assert isinstance(gen.iter.typ, InstanceType), "Only lists are valid generators"
        assert isinstance(gen.iter.typ.typ, ListType), "Only lists are valid generators"
        assert isinstance(
            gen.target, Name
        ), "Can only assign value to singleton element"
        lst = plt.Apply(self.visit(gen.iter), plt.Var(STATEMONAD))
        ifs = None
        for ifexpr in gen.ifs:
            if ifs is None:
                ifs = self.visit(ifexpr)
            else:
                ifs = plt.And(ifs, self.visit(ifexpr))
        map_fun = plt.Lambda(
            ["x"],
            plt.Apply(
                self.visit(node.elt),
                extend_statemonad([gen.target.id], [plt.Var("x")], plt.Var(STATEMONAD)),
            ),
        )
        empty_list_con = empty_list(node.elt.typ)
        if ifs is not None:
            filter_fun = plt.Lambda(
                ["x"],
                plt.Apply(
                    ifs,
                    extend_statemonad(
                        [gen.target.id], [plt.Var("x")], plt.Var(STATEMONAD)
                    ),
                ),
            )
            return plt.Lambda(
                [STATEMONAD],
                plt.MapFilterList(
                    lst,
                    filter_fun,
                    map_fun,
                    empty_list_con,
                ),
            )
        else:
            return plt.Lambda(
                [STATEMONAD],
                plt.MapList(
                    lst,
                    map_fun,
                    empty_list_con,
                ),
            )

    def generic_visit(self, node: AST) -> plt.AST:
        raise NotImplementedError(f"Can not compile {node}")


class OptimizeConstantFolding(CompilingNodeTransformer):
    step = "Constant folding"

    def generic_visit(self, node: AST):
        node = super().generic_visit(node)
        if not isinstance(node, expr):
            # only evaluate expressions, not statements
            return node
        if isinstance(node, Constant):
            # prevents unneccessary computations
            return node
        node_source = unparse(node)
        if "print(" in node_source:
            # do not optimize away print statements
            return node
        try:
            # TODO we can add preceding plutusdata definitions here!
            node_eval = eval(node_source, globals(), {})
        except Exception as e:
            return node

        def rec_dump(c):
            if any(isinstance(c, a) for a in ACCEPTED_ATOMIC_TYPES):
                new_node = Constant(c, None)
                copy_location(new_node, node)
                return new_node
            if isinstance(c, list):
                return List([rec_dump(ce) for ce in c], Load())
            if isinstance(c, dict):
                return Dict(
                    [rec_dump(ce) for ce in c.keys()],
                    [rec_dump(ce) for ce in c.values()],
                )

        if any(isinstance(node_eval, t) for t in ACCEPTED_ATOMIC_TYPES + [list, dict]):
            return rec_dump(node_eval)
        return node
