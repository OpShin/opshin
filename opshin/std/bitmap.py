"""
The BitMap library provides tools to interact with a highly efficient datastructure
that stores boolean values with minimal overhead (1 bit per bool)
"""
BitMap = bytes

BYTE_SIZE = 8
POWS = [2**i for i in range(BYTE_SIZE)]


def init_bitmap(size: int) -> BitMap:
    """Creates an empty bitmap with size bits"""
    return b"\x00" * ((size + BYTE_SIZE - 1) // BYTE_SIZE)


def test_bitmap(bmp: BitMap, i: int) -> bool:
    """Tests if bit at position i has been set to 1"""
    byte = bmp[i // BYTE_SIZE]
    bit = (byte // POWS[(BYTE_SIZE - 1) - (i % BYTE_SIZE)]) % 2
    return bit == 1


def _set_bitmap(bmp: BitMap, i: int, v: bool) -> BitMap:
    """
    Sets a bit in the bitmap to the specified value
    i: index of the value to set
    v: value of the bit to be set (0 or 1)
    """
    scaled_i = i // BYTE_SIZE
    byte = bmp[scaled_i]
    powi = POWS[(BYTE_SIZE - 1) - (i % BYTE_SIZE)]
    bit = (byte // powi) % 2
    if bit == v:
        new_byte = byte
    elif not v:
        # v == 0
        new_byte = byte - powi
    else:
        # v == 1
        new_byte = byte + powi
    return bmp[:scaled_i] + bytes([new_byte]) + bmp[scaled_i + 1 :]


def set_bitmap(bmp: BitMap, i: int) -> BitMap:
    """Sets a bit in the bitmap to 1"""
    return _set_bitmap(bmp, i, True)


def reset_bitmap(bmp: BitMap, i: int) -> BitMap:
    """Sets a bit in the bitmap to 0"""
    return _set_bitmap(bmp, i, False)


def flip_bitmap(bmp: BitMap, i: int) -> BitMap:
    """Flips a bit in the bitmap"""
    scaled_i = i // BYTE_SIZE
    byte = bmp[scaled_i]
    powi = POWS[(BYTE_SIZE - 1) - (i % BYTE_SIZE)]
    bit = (byte // powi) % 2
    if bit == 1:
        # v == 0
        new_byte = byte - powi
    else:
        # v == 1
        new_byte = byte + powi
    return bmp[:scaled_i] + bytes([new_byte]) + bmp[scaled_i + 1 :]


def size_bitmap(bmp: BitMap) -> int:
    """Returns the size of the bitmap in bits"""
    return len(bmp) * BYTE_SIZE


def any_bitmap(b: BitMap) -> bool:
    """Returns whether any bit was set to 1"""
    return b != (b"\x00" * len(b))


def all_bitmap(b: BitMap) -> bool:
    """Returns whether all bits were set to 1"""
    return b == (b"\xFF" * len(b))


def none_bitmap(b: BitMap) -> bool:
    """Returns whether no bits were set to 1"""
    return b == (b"\x00" * len(b))
