from ast import Assign, Constant, Name, Subscript
import typing

from ..typed_ast import TypedDestructuringAssign, typedstmt
from ..typed_util import ScopedSequenceNodeTransformer


class RewriteDestructuringAssign(ScopedSequenceNodeTransformer):
    step = "Lowering destructuring assignments"

    def _match_destructuring_assignments(
        self, node_seq: typing.List[typedstmt], index: int
    ) -> typing.Optional[tuple[Assign, typing.List[Assign]]]:
        if index >= len(node_seq):
            return None
        assignment = node_seq[index]
        if not (
            isinstance(assignment, Assign)
            and len(assignment.targets) == 1
            and isinstance(assignment.targets[0], Name)
        ):
            return None
        destructure_metadata = getattr(assignment, "destructure_metadata", None)
        if destructure_metadata is None or destructure_metadata.kind != "assignment":
            return None
        extraction_count = destructure_metadata.length
        if extraction_count is None:
            return None
        source_name = assignment.targets[0].id
        extractions = []
        for offset in range(extraction_count):
            extraction_index = index + offset + 1
            if extraction_index >= len(node_seq):
                return None
            extraction = node_seq[extraction_index]
            extraction_metadata = getattr(extraction, "destructure_metadata", None)
            if not (
                isinstance(extraction, Assign)
                and len(extraction.targets) == 1
                and isinstance(extraction.targets[0], Name)
                and isinstance(extraction.value, Subscript)
                and isinstance(extraction.value.value, Name)
                and extraction.value.value.id == source_name
                and isinstance(extraction.value.slice, Constant)
                and extraction.value.slice.value == offset
                and extraction_metadata is not None
                and extraction_metadata.kind == "extraction"
                and extraction_metadata.index == offset
            ):
                return None
            extractions.append(extraction)
        return assignment, extractions

    def _rewrite_sequence(
        self, node_seq: typing.List[typedstmt]
    ) -> typing.List[typedstmt]:
        rewritten = []
        i = 0
        while i < len(node_seq):
            destructuring_group = self._match_destructuring_assignments(node_seq, i)
            if destructuring_group is None:
                rewritten.append(node_seq[i])
                i += 1
                continue
            assignment, extractions = destructuring_group
            lowered = TypedDestructuringAssign()
            lowered.value = assignment.value
            lowered.targets = [extraction.targets[0] for extraction in extractions]
            lowered.element_typs = [extraction.value.typ for extraction in extractions]
            for attr in lowered._attributes:
                if hasattr(assignment, attr):
                    setattr(lowered, attr, getattr(assignment, attr))
            rewritten.append(lowered)
            i += len(extractions) + 1
        return rewritten

    def visit_sequence(self, body: list[typedstmt]) -> list[typedstmt]:
        return self._rewrite_sequence(super().visit_sequence(body))
