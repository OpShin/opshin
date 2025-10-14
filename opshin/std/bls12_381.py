from pyblst import BlstP1Element, BlstP2Element, BlstFP12Element


class BLS12381G1Element:
    _value: BlstP1Element

    def __init__(self, value: BlstP1Element):
        if not isinstance(value, BlstP1Element):
            raise TypeError("value must be a BlstP1Element")
        self._value = value

    def compress(self) -> bytes:
        return self._value.compress()

    def __eq__(self, other) -> bool:
        if not isinstance(other, BLS12381G1Element):
            raise TypeError("Can only compare BLS12381G1Element with BLS12381G1Element")
        return self._value == other._value

    def __add__(self, other) -> "BLS12381G1Element":
        if not isinstance(other, BLS12381G1Element):
            raise TypeError("Can only add BLS12381G1Element with BLS12381G1Element")
        return BLS12381G1Element(value=self._value + other._value)

    def __neg__(self) -> "BLS12381G1Element":
        return BLS12381G1Element(value=-self._value)

    def __pos__(self) -> "BLS12381G1Element":
        return BLS12381G1Element(value=self._value)

    def __sub__(self, other):
        if not isinstance(other, BLS12381G1Element):
            raise TypeError(
                "Can only subtract BLS12381G1Element with BLS12381G1Element"
            )
        return BLS12381G1Element(value=self._value + (-other._value))

    def __mul__(self, other) -> "BLS12381G1Element":
        return self.scalar_mul(other)

    def __rmul__(self, other) -> "BLS12381G1Element":
        return self.__mul__(other)

    def scalar_mul(self, other) -> "BLS12381G1Element":
        if not isinstance(other, int):
            raise TypeError("Can only multiply BLS12381G1Element with int")
        return BLS12381G1Element(value=self._value.scalar_mul(other))


class BLS12381G2Element:
    _value: BlstP2Element

    def __init__(self, value: BlstP2Element):
        if not isinstance(value, BlstP2Element):
            raise TypeError("value must be a BlstP2Element")
        self._value = value

    def compress(self) -> bytes:
        return self._value.compress()

    def __eq__(self, other) -> bool:
        if not isinstance(other, BLS12381G2Element):
            raise TypeError("Can only compare BLS12381G2Element with BLS12381G2Element")
        return self._value == other._value

    def __add__(self, other) -> "BLS12381G2Element":
        if not isinstance(other, BLS12381G2Element):
            raise TypeError("Can only add BLS12381G2Element with BLS12381G2Element")
        return BLS12381G2Element(value=self._value + other._value)

    def __sub__(self, other) -> "BLS12381G2Element":
        if not isinstance(other, BLS12381G2Element):
            raise TypeError(
                "Can only subtract BLS12381G2Element with BLS12381G2Element"
            )
        return BLS12381G2Element(value=self._value + (-other._value))

    def __neg__(self) -> "BLS12381G2Element":
        return BLS12381G2Element(value=-self._value)

    def __pos__(self) -> "BLS12381G2Element":
        return BLS12381G2Element(value=self._value)

    def __mul__(self, other) -> "BLS12381G2Element":
        return self.scalar_mul(other)

    def __rmul__(self, other) -> "BLS12381G2Element":
        return self.__mul__(other)

    def scalar_mul(self, other) -> "BLS12381G2Element":
        if not isinstance(other, int):
            raise TypeError("Can only multiply BLS12381G2Element with int")
        return BLS12381G2Element(value=self._value.scalar_mul(other))


class BLS12381MillerLoopResult:
    _value: BlstFP12Element

    def __init__(self, value: BlstFP12Element):
        if not isinstance(value, BlstFP12Element):
            raise TypeError("value must be a BlstFP12Element")
        self._value = value

    def __mul__(self, other) -> "BLS12381MillerLoopResult":
        if not isinstance(other, BLS12381MillerLoopResult):
            raise TypeError(
                "Can only multiply BLS12381MillerLoopResult with BLS12381MillerLoopResult"
            )
        return BLS12381MillerLoopResult(value=self._value * other._value)
