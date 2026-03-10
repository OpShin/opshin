import argparse
from opshin.optimize.optimize_selective_narrowing_rebind import (
    BYTESTRING_REBIND_READ_THRESHOLD,
    INTEGER_REBIND_READ_THRESHOLD,
    LIST_REBIND_READ_THRESHOLD,
    forced_beats_noop,
)

DEFAULT_MAX_READS = 10


def find_threshold(
    kind: str,
    max_reads: int,
    low: int = 1,
) -> int | None:
    if max_reads < low:
        raise AssertionError("max_reads must be at least 1")
    if not forced_beats_noop(kind, max_reads):
        return None
    left = low
    right = max_reads
    while left < right:
        mid = (left + right) // 2
        if forced_beats_noop(kind, mid):
            right = mid
        else:
            left = mid + 1
    return left


def report(kind: str, measured: int | None, configured: int | None, max_reads: int):
    if measured is None:
        print(f"{kind}: none up to {max_reads} (configured={configured})")
        return
    print(f"{kind}: measured={measured} configured={configured}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "kinds",
        nargs="+",
        choices=("list", "int", "bytes", "dict"),
    )
    parser.add_argument(
        "--max-reads",
        type=int,
        default=DEFAULT_MAX_READS,
    )
    args = parser.parse_args()

    configured_thresholds = {
        "list": LIST_REBIND_READ_THRESHOLD,
        "int": INTEGER_REBIND_READ_THRESHOLD,
        "bytes": BYTESTRING_REBIND_READ_THRESHOLD,
        "dict": None,
    }

    for kind in args.kinds:
        report(
            kind,
            find_threshold(kind, args.max_reads),
            configured_thresholds[kind],
            args.max_reads,
        )


if __name__ == "__main__":
    main()
