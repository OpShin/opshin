from hypothesis import given, strategies as st

from opshin.ledger.interval import *


@given(a=st.integers(), b=st.integers(), c=st.integers())
def test_ordering_compare(a: int, b: int, c: int) -> None:
    left = compare(a, b)
    right = compare(b, c)
    outer = compare(a, c)
    # The 6 permutations will match one of 3 combinations
    if left == right:
        assert outer == right, (left, outer, right)
    elif -left == outer:
        assert right == outer, (left, outer, right)
    elif right == -outer:
        assert left == outer, (left, outer, right)


@given(a=st.integers(), b=st.integers())
def test_commutative_compare_extended(a: int, b: int) -> None:
    left = compare(a, b)
    right = compare(b, a)
    assert left == -right, (left, right)


compare_extended_operands = st.one_of(
    st.builds(FinitePOSIXTime), st.builds(NegInfPOSIXTime), st.builds(PosInfPOSIXTime)
)


@given(
    a=compare_extended_operands,
    b=compare_extended_operands,
    c=compare_extended_operands,
)
def test_ordering_compare_extended(
    a: ExtendedPOSIXTime,
    b: ExtendedPOSIXTime,
    c: ExtendedPOSIXTime,
) -> None:
    left = compare_extended(a, b)
    right = compare_extended(b, c)
    outer = compare_extended(a, c)
    # The 6 permutations will match one of 3 combinations
    if left == right:
        assert outer == right, (left, outer, right)
    elif -left == outer:
        assert right == outer, (left, outer, right)
    elif right == -outer:
        assert left == outer, (left, outer, right)


@given(a=compare_extended_operands, b=compare_extended_operands)
def test_commutative_compare_extended(
    a: ExtendedPOSIXTime,
    b: ExtendedPOSIXTime,
) -> None:
    left = compare_extended(a, b)
    right = compare_extended(b, a)
    assert left == -right, (left, right)


compare_lower_bound_operands = st.builds(LowerBoundPOSIXTime)


@given(
    a=compare_lower_bound_operands,
    b=compare_lower_bound_operands,
    c=compare_lower_bound_operands,
)
def test_ordering_compare_lower_bound(
    a: LowerBoundPOSIXTime,
    b: LowerBoundPOSIXTime,
    c: LowerBoundPOSIXTime,
) -> None:
    left = compare_lower_bound(a, b)
    right = compare_lower_bound(b, c)
    outer = compare_lower_bound(a, c)
    # The 6 permutations will match one of 3 combinations
    if left == right:
        assert outer == right, (left, outer, right)
    elif -left == outer:
        assert right == outer, (left, outer, right)
    elif right == -outer:
        assert left == outer, (left, outer, right)


@given(a=compare_lower_bound_operands, b=compare_lower_bound_operands)
def test_commutative_lower_bound(
    a: LowerBoundPOSIXTime,
    b: LowerBoundPOSIXTime,
) -> None:
    left = compare_lower_bound(a, b)
    right = compare_lower_bound(b, a)
    assert left == -right, (left, right)


compare_upper_bound_operands = st.builds(UpperBoundPOSIXTime)


@given(
    a=compare_upper_bound_operands,
    b=compare_upper_bound_operands,
    c=compare_upper_bound_operands,
)
def test_ordering_compare_upper_bound(
    a: UpperBoundPOSIXTime,
    b: UpperBoundPOSIXTime,
    c: UpperBoundPOSIXTime,
) -> None:
    left = compare_upper_bound(a, b)
    right = compare_upper_bound(b, c)
    outer = compare_upper_bound(a, c)
    # The 6 permutations will match one of 3 combinations
    if left == right:
        assert outer == right, (left, outer, right)
    elif -left == outer:
        assert right == outer, (left, outer, right)
    elif right == -outer:
        assert left == outer, (left, outer, right)


@given(a=compare_upper_bound_operands, b=compare_upper_bound_operands)
def test_commutative_compare_upper_bound(
    a: UpperBoundPOSIXTime,
    b: UpperBoundPOSIXTime,
) -> None:
    left = compare_upper_bound(a, b)
    right = compare_upper_bound(b, a)
    assert left == -right, (left, right)


contains_operands = st.builds(POSIXTimeRange)


@given(a=contains_operands, b=contains_operands)
def test_contains(a: POSIXTimeRange, b: POSIXTimeRange):
    lower = compare_lower_bound(a.lower_bound, b.lower_bound)
    upper = compare_upper_bound(a.upper_bound, b.upper_bound)
    if contains(a, b):
        assert lower == 1 or lower == 0
        assert upper == 0 or upper == -1
    else:
        assert lower == -1 or upper == 1


@given(
    lower_bound=st.integers(),
)
def test_fuzz_make_from(
    lower_bound: int,
) -> None:
    make_from(lower_bound=lower_bound)


@given(
    lower_bound=st.integers(),
    upper_bound=st.integers(),
)
def test_fuzz_make_range(
    lower_bound: int,
    upper_bound: int,
) -> None:
    make_range(
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )


@given(
    upper_bound=st.integers(),
)
def test_fuzz_make_to(
    upper_bound: int,
) -> None:
    make_to(upper_bound=upper_bound)


@given(
    time=st.one_of(
        st.builds(FinitePOSIXTime),
        st.builds(NegInfPOSIXTime),
        st.builds(PosInfPOSIXTime),
    )
)
def test_fuzz_compare_extended_helper(time: ExtendedPOSIXTime) -> None:
    compare_extended_helper(time)


@given(b=st.booleans())
def test_get_bool(b: bool) -> None:
    if b:
        bool_data = TrueData()
    else:
        bool_data = FalseData()
    assert get_bool(bool_data) == b


@given(
    lower_bound=st.integers(),
    upper_bound_1=st.integers(),
    upper_bound_2=st.integers(),
)
def test_make_to_in_make_range(
    lower_bound: int,
    upper_bound_1: int,
    upper_bound_2: int,
) -> None:
    assert contains(
        make_to(upper_bound=upper_bound_1), make_range(lower_bound, upper_bound_2)
    ) == (upper_bound_1 >= upper_bound_2)


@given(
    lower_bound_1=st.integers(),
    lower_bound_2=st.integers(),
    upper_bound=st.integers(),
)
def test_make_from_in_make_range(
    lower_bound_1: int,
    lower_bound_2: int,
    upper_bound: int,
) -> None:
    assert contains(
        make_from(lower_bound=lower_bound_1), make_range(lower_bound_2, upper_bound)
    ) == (lower_bound_1 <= lower_bound_2)
