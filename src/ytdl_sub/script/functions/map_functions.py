from typing import Optional

from ytdl_sub.script.types.array import Array
from ytdl_sub.script.types.array import ResolvedArray
from ytdl_sub.script.types.map import Map
from ytdl_sub.script.types.resolvable import AnyArgument
from ytdl_sub.script.types.resolvable import Boolean
from ytdl_sub.script.types.resolvable import Hashable
from ytdl_sub.script.types.resolvable import Integer
from ytdl_sub.script.types.resolvable import Lambda2
from ytdl_sub.script.types.resolvable import Lambda3
from ytdl_sub.script.utils.exceptions import KeyDoesNotExistRuntimeException


class MapFunctions:
    @staticmethod
    def map_get(mapping: Map, key: Hashable, default: Optional[AnyArgument] = None) -> AnyArgument:
        """
        Return ``key``'s value within the Map. If ``key`` does not exist, and ``default`` is
        provided, it will return ``default``. Otherwise, will error.
        """
        if key not in mapping.value:
            if default is not None:
                return default

            raise KeyDoesNotExistRuntimeException(
                f"Tried to call %map_get with key {key.value}, but it does not exist"
            )
        return mapping.value[key]

    @staticmethod
    def map_contains(mapping: Map, key: Hashable) -> Boolean:
        """
        Returns True if the key is in the Map. False otherwise.
        """
        return Boolean(key in mapping.value)

    # pylint: disable=unused-argument

    @staticmethod
    def map_apply(mapping: Map, lambda_function: Lambda2) -> Array:
        """
        Apply a lambda function on the Map, where each arg
        passed to the lambda function is ``key, value`` as two separate args.
        """
        return ResolvedArray([ResolvedArray([key, value]) for key, value in mapping.value.items()])

    @staticmethod
    def map_enumerate(mapping: Map, lambda_function: Lambda3) -> Array:
        """
        Apply a lambda function on the Map, where each arg
        passed to the lambda function is ``idx, key, value`` as three separate args.
        """
        return ResolvedArray(
            [
                ResolvedArray([Integer(idx), key_value[0], key_value[1]])
                for idx, key_value in enumerate(mapping.value.items())
            ]
        )
