BitMap = bytes

BYTE_SIZE = 8
POWS = [2**i for i in range(BYTE_SIZE)]


def init_bitmap(size: int):
    return b"\x00" * ((size + BYTE_SIZE - 1) // BYTE_SIZE)


def isset_bitmap(bmp: BitMap, i: int) -> bool:
    byte = bmp[i // BYTE_SIZE]
    bit = (byte // POWS[(BYTE_SIZE - 1) - (i % BYTE_SIZE)]) % 2
    return bit == 1


def set_bitmap(bmp: BitMap, i: int, v: bool) -> BitMap:
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
