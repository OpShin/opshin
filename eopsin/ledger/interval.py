from eopsin.prelude import *


def compare(a: int, b: int) -> int:
    # a < b: 1
    # a == b: 0
    # a > b: -1
    if a < b:
        result = 1
    elif a == b:
        result = 0
    else:
        result = -1
    return result


def compare_extended_helper(time: ExtendedPOSIXTime) -> int:
    result = 0
    if isinstance(time, NegInfPOSIXTime):
        result = -1
    elif isinstance(time, FinitePOSIXTime):
        result = 0
    elif isinstance(time, PosInfPOSIXTime):
        result = 1
    return result


def compare_extended(a: ExtendedPOSIXTime, b: ExtendedPOSIXTime) -> int:
    # a < b: 1
    # a == b: 0
    # a > b: -1
    a_val = compare_extended_helper(a)
    b_val = compare_extended_helper(b)
    if a_val == 0 and b_val == 0:
        a_finite: FinitePOSIXTime = a
        b_finite: FinitePOSIXTime = b
        result = compare(a_finite.time, b_finite.time)
    else:
        result = compare(a_val, b_val)
    return result


def get_bool(b: BoolData) -> bool:
    if isinstance(b, TrueData):
        result = True
    else:
        result = False
    return result


def compare_upper_bound(a: UpperBoundPOSIXTime, b: UpperBoundPOSIXTime) -> int:
    # a < b: 1
    # a == b: 0
    # a > b: -1
    result = compare_extended(a.limit, b.limit)
    if result == 0:
        a_val = 1 if get_bool(a.closed) else 0
        b_val = 1 if get_bool(b.closed) else 0
        result = compare(a_val, b_val)
    return result


def compare_lower_bound(a: LowerBoundPOSIXTime, b: LowerBoundPOSIXTime) -> int:
    # a < b: 1
    # a == b: 0
    # a > b: -1
    result = compare_extended(a.limit, b.limit)
    if result == 0:
        a_val = 1 if get_bool(a.closed) else 0
        b_val = 1 if get_bool(b.closed) else 0
        result = compare(b_val, a_val)
    return result


def contains(a: POSIXTimeRange, b: POSIXTimeRange) -> bool:
    # Returns True if the interval `b` is entirely contained in `a`.
    lower = compare_lower_bound(a.lower_bound, b.lower_bound)
    upper = compare_upper_bound(a.upper_bound, b.upper_bound)
    return (lower == 1 or lower == 0) and (upper == 0 or upper == -1)


def make_range(
    lower_bound: POSIXTime,
    upper_bound: POSIXTime,
    lower_closed: BoolData,
    upper_closed: BoolData,
) -> POSIXTimeRange:
    return POSIXTimeRange(
        LowerBoundPOSIXTime(FinitePOSIXTime(lower_bound), lower_closed),
        UpperBoundPOSIXTime(FinitePOSIXTime(upper_bound), upper_closed),
    )


def make_from(lower_bound: POSIXTime, lower_closed: BoolData) -> POSIXTimeRange:
    return POSIXTimeRange(
        LowerBoundPOSIXTime(FinitePOSIXTime(lower_bound), lower_closed),
        UpperBoundPOSIXTime(PosInfPOSIXTime(), TrueData()),
    )


def make_to(upper_bound: POSIXTime, upper_closed: BoolData) -> POSIXTimeRange:
    return POSIXTimeRange(
        LowerBoundPOSIXTime(NegInfPOSIXTime(), TrueData()),
        UpperBoundPOSIXTime(FinitePOSIXTime(upper_bound), upper_closed),
    )


def make_lower_bound(time: POSIXTime) -> LowerBoundPOSIXTime:
    return LowerBoundPOSIXTime(FinitePOSIXTime(time), TrueData())


def make_upper_bound(time: POSIXTime) -> UpperBoundPOSIXTime:
    return UpperBoundPOSIXTime(FinitePOSIXTime(time), TrueData())


def make_strict_lower_bound(time: POSIXTime) -> LowerBoundPOSIXTime:
    return LowerBoundPOSIXTime(FinitePOSIXTime(time), FalseData())


def make_strict_upper_bound(time: POSIXTime) -> UpperBoundPOSIXTime:
    return UpperBoundPOSIXTime(FinitePOSIXTime(time), FalseData())


def min_lower(a: LowerBoundPOSIXTime, b: LowerBoundPOSIXTime) -> LowerBoundPOSIXTime:
    if compare_lower_bound(a, b) == 1:
        result = a
    else:
        result = b
    return result


def max_lower(a: LowerBoundPOSIXTime, b: LowerBoundPOSIXTime) -> LowerBoundPOSIXTime:
    if compare_lower_bound(a, b) == 1:
        result = b
    else:
        result = a
    return result


def min_upper(a: UpperBoundPOSIXTime, b: UpperBoundPOSIXTime) -> UpperBoundPOSIXTime:
    if compare_upper_bound(a, b) == 1:
        result = a
    else:
        result = b
    return result


def max_upper(a: UpperBoundPOSIXTime, b: UpperBoundPOSIXTime) -> UpperBoundPOSIXTime:
    if compare_upper_bound(a, b) == 1:
        result = b
    else:
        result = a
    return result


def make_interval(a: POSIXTime, b: POSIXTime) -> POSIXTimeRange:
    return POSIXTimeRange(make_lower_bound(a), make_upper_bound(b))


def make_singleton(time: POSIXTime) -> POSIXTimeRange:
    return make_interval(time, time)


def member(time: POSIXTime, a: POSIXTimeRange) -> bool:
    return contains(a, make_singleton(time))


def intersection(a: POSIXTimeRange, b: POSIXTimeRange) -> POSIXTimeRange:
    return POSIXTimeRange(
        max_lower(a.lower_bound, b.lower_bound), min_upper(a.upper_bound, b.upper_bound)
    )


def hull(a: POSIXTimeRange, b: POSIXTimeRange) -> POSIXTimeRange:
    return POSIXTimeRange(
        min_lower(a.lower_bound, b.lower_bound), max_upper(a.upper_bound, b.upper_bound)
    )


def is_empty(a: POSIXTimeRange) -> bool:
    c = compare_extended(a.lower_bound.limit, a.upper_bound.limit)
    result = False
    if c == -1:
        if not get_bool(a.lower_bound.closed) and not get_bool(a.upper_bound.closed):
            left = a.lower_bound.limit
            right = a.upper_bound.limit
            if isinstance(left, FinitePOSIXTime):
                if isinstance(right, FinitePOSIXTime):
                    result = compare(left.time + 1, right.time) == 0
    elif c == 1:
        result = True
    else:
        result = not (get_bool(a.lower_bound.closed) and get_bool(a.upper_bound.closed))
    return result


def overlaps(a: POSIXTimeRange, b: POSIXTimeRange) -> bool:
    return not is_empty(intersection(a, b))


def before(time: POSIXTime, a: POSIXTimeRange) -> bool:
    return compare_lower_bound(make_lower_bound(time), a.lower_bound) == 1


def after(time: POSIXTime, a: POSIXTimeRange) -> bool:
    return compare_upper_bound(make_upper_bound(time), a.upper_bound) == -1
