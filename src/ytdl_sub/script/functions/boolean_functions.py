from ytdl_sub.script.types.resolvable import AnyType
from ytdl_sub.script.types.resolvable import Boolean


class BooleanFunctions:
    @staticmethod
    def bool(value: AnyType) -> Boolean:
        """
        Cast any type to a boolean
        """
        return Boolean(bool(value.value))

    @staticmethod
    def equals(left: AnyType, right: AnyType) -> Boolean:
        """
        Returns True if left equals right. False otherwise.
        """
        return Boolean(left.value == right.value)

    @staticmethod
    def lt(left: AnyType, right: AnyType) -> Boolean:
        return Boolean(left.value < right.value)

    @staticmethod
    def lte(left: AnyType, right: AnyType) -> Boolean:
        return Boolean(left.value <= right.value)

    @staticmethod
    def gt(left: AnyType, right: AnyType) -> Boolean:
        return Boolean(left.value > right.value)

    @staticmethod
    def gte(left: AnyType, right: AnyType) -> Boolean:
        return Boolean(left.value >= right.value)

    @staticmethod
    def and_(left: Boolean, right: Boolean) -> Boolean:
        return Boolean(left.value and right.value)

    @staticmethod
    def or_(left: Boolean, right: Boolean) -> Boolean:
        return Boolean(left.value or right.value)

    @staticmethod
    def xor(left: Boolean, right: Boolean) -> Boolean:
        return Boolean(left.value ^ right.value)

    @staticmethod
    def not_(value: Boolean) -> Boolean:
        return Boolean(not value.value)
