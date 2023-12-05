from typing import List
from typing import Optional

from ytdl_sub.script.types.array import Array
from ytdl_sub.script.types.array import ResolvedArray
from ytdl_sub.script.types.resolvable import AnyArgument
from ytdl_sub.script.types.resolvable import Boolean
from ytdl_sub.script.types.resolvable import Integer
from ytdl_sub.script.types.resolvable import Lambda
from ytdl_sub.script.types.resolvable import LambdaTwo
from ytdl_sub.script.types.resolvable import Resolvable
from ytdl_sub.script.utils.exceptions import UNREACHABLE
from ytdl_sub.script.utils.exceptions import ArrayValueDoesNotExist


class ArrayFunctions:
    @staticmethod
    def array_extend(*arrays: Array) -> Array:
        """
        Combine multiple Arrays into a single Array.
        """
        output: List[Resolvable] = []
        for array in arrays:
            output.extend(array.value)

        return ResolvedArray(output)

    @staticmethod
    def array_at(array: Array, idx: Integer) -> Resolvable:
        """
        Return the element in the Array at index ``idx``.
        """
        return array.value[idx.value]

    @staticmethod
    def array_contains(array: Array, value: AnyArgument) -> Boolean:
        """
        Return True if the value exists in the Array. False otherwise.
        """
        return Boolean(value in array.value)

    @staticmethod
    def array_index(array: Array, value: AnyArgument) -> Integer:
        """
        Return the index of the value within the Array if it exists. If it does not, it will
        throw an error.
        """
        if not ArrayFunctions.array_contains(array=array, value=value):
            raise ArrayValueDoesNotExist(
                "Tried to get the index of a value in an Array that does not exist"
            )

        if isinstance(value, Resolvable):
            return Integer(array.value.index(value))

        raise UNREACHABLE

    @staticmethod
    def array_slice(array: Array, start: Integer, end: Optional[Integer] = None) -> Array:
        """
        Returns the slice of the Array.
        """
        if end is not None:
            return ResolvedArray(array.value[start.value : end.value])
        return ResolvedArray(array.value[start.value :])

    @staticmethod
    def array_flatten(array: Array) -> Array:
        """
        Flatten any nested Arrays into a single-dimensional Array.
        """
        output: List[Resolvable] = []
        for elem in array.value:
            if isinstance(elem, Array):
                output.extend(ArrayFunctions.array_flatten(elem).value)
            else:
                output.append(elem)

        return ResolvedArray(output)

    @staticmethod
    def array_reverse(array: Array) -> Array:
        """
        Reverse an Array.
        """
        return ResolvedArray(list(reversed(array.value)))

    # pylint: disable=unused-argument

    @staticmethod
    def array_apply(array: Array, lambda_function: Lambda) -> Array:
        """
        Apply a lambda function on every element in the Array.
        """
        return ResolvedArray([ResolvedArray([val]) for val in array.value])

    @staticmethod
    def array_enumerate(array: Array, lambda_function: LambdaTwo) -> Array:
        """
        Apply a lambda function on every element in the Array, where each arg
        passed to the lambda function is ``idx, element`` as two separate args.
        """
        return ResolvedArray(
            [ResolvedArray([Integer(idx), val]) for idx, val in enumerate(array.value)]
        )

    # pylint: enable=unused-argument
