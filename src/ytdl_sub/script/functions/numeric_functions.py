from ytdl_sub.script.types.resolvable import Float
from ytdl_sub.script.types.resolvable import Integer
from ytdl_sub.script.types.resolvable import Numeric
from ytdl_sub.script.types.resolvable import AnyType


def _to_numeric(value: int | float) -> Numeric:
    if int(value) == value:
        return Integer(value=value)
    return Float(value=value)


class NumericFunctions:
    @staticmethod
    def float(value: AnyType) -> Float:
        return Float(value=float(value.value))

    @staticmethod
    def int(value: AnyType) -> Integer:
        return Integer(value=int(value.value))

    @staticmethod
    def add(left: Numeric, right: Numeric) -> Numeric:
        return _to_numeric(left.value + right.value)

    @staticmethod
    def sub(left: Numeric, right: Numeric) -> Numeric:
        return _to_numeric(left.value - right.value)

    @staticmethod
    def mul(left: Numeric, right: Numeric) -> Numeric:
        return _to_numeric(left.value * right.value)

    @staticmethod
    def div(left: Numeric, right: Numeric) -> Numeric:
        return _to_numeric(left.value / right.value)

    @staticmethod
    def mod(value: Integer, modulo: Integer) -> Integer:
        return Integer(value=value.value % modulo.value)

    @staticmethod
    def max(left: Numeric, right: Numeric) -> Numeric:
        return _to_numeric(max(left.value, right.value))

    @staticmethod
    def min(left: Numeric, right: Numeric) -> Numeric:
        return _to_numeric(min(left.value, right.value))
