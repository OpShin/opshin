"""
The BitMap library provides tools to interact with a highly efficient datastructure
that stores boolean values with minimal overhead (1 bit per bool)
"""

from opshin.std.builtins import *

BitMap = bytes

BYTE_SIZE = 8
POWS = [2 ** (BYTE_SIZE - i - 1) for i in range(BYTE_SIZE)]


def init_bitmap(size: int) -> BitMap:
    """Creates an empty bitmap with size bits"""
    return replicate_byte(((size + BYTE_SIZE - 1) // BYTE_SIZE), 0)


def test_bitmap(bmp: BitMap, i: int) -> bool:
    """Tests if bit at position i has been set to 1"""
    return read_bit(bmp, i)


def set_bitmap(bmp: BitMap, i: List[int]) -> BitMap:
    """Sets bits of the bitmap at indices specified by i to 1"""
    return write_bits(bmp, i, True)


def reset_bitmap(bmp: BitMap, i: List[int]) -> BitMap:
    """Sets bits of the bitmap at indices specified by i to 0"""
    return write_bits(bmp, i, False)


def flip_bitmap(bmp: BitMap, i: int) -> BitMap:
    """Flips a bit in the bitmap"""
    prev_val = read_bit(bmp, i)
    return write_bits(bmp, [i], not prev_val)


def size_bitmap(bmp: BitMap) -> int:
    """Returns the size of the bitmap in bits"""
    return len(bmp) * BYTE_SIZE


def any_bitmap(b: BitMap) -> bool:
    """Returns whether any bit was set to 1"""
    return count_set_bits(b) > 0


def all_bitmap(b: BitMap) -> bool:
    """Returns whether all bits were set to 1"""
    return count_set_bits(b) == size_bitmap(b)


def none_bitmap(b: BitMap) -> bool:
    """Returns whether no bits were set to 1"""
    return count_set_bits(b) == 0
