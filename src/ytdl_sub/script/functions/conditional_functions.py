from typing import Union

from ytdl_sub.script.types.resolvable import AnyTypeReturnableA
from ytdl_sub.script.types.resolvable import AnyTypeReturnableB
from ytdl_sub.script.types.resolvable import Boolean


class ConditionalFunctions:
    @staticmethod
    def if_(
        condition: Boolean, true: AnyTypeReturnableA, false: AnyTypeReturnableB
    ) -> Union[AnyTypeReturnableA, AnyTypeReturnableB]:
        """
        Conditional ``if`` statement that returns the ``true`` or ``false`` parameter
        depending on the ``condition`` value.
        """
        if condition.value:
            return true
        return false
