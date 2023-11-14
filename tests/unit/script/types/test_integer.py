import re
from typing import Tuple

import pytest

from ytdl_sub.script.parser import NUMERICS_INVALID_CHAR
from ytdl_sub.script.parser import NUMERICS_ONLY_ARGS
from ytdl_sub.script.parser import UNEXPECTED_CHAR_ARGUMENT
from ytdl_sub.script.parser import UNEXPECTED_COMMA_ARGUMENT
from ytdl_sub.script.parser import ArgumentParser
from ytdl_sub.script.script import Script
from ytdl_sub.script.types.array import ResolvedArray
from ytdl_sub.script.types.resolvable import Float
from ytdl_sub.script.types.resolvable import Integer
from ytdl_sub.script.types.resolvable import String
from ytdl_sub.script.utils.exceptions import InvalidSyntaxException


class TestInteger:
    @pytest.mark.parametrize(
        "integer",
        [
            "{1}",
            "{  1  }",
            "{-1}",
            "{   -1   }",
            "{0001}",
            "{  0001   }",
        ],
    )
    def test_integer_not_arg(self, integer: str):
        with pytest.raises(InvalidSyntaxException, match=re.escape(str(NUMERICS_ONLY_ARGS))):
            Script({"integer": integer}).resolve()

    @pytest.mark.parametrize(
        "integer, expected_integer",
        [
            ("{%int(1)}", 1),
            ("{%int(  1  )}", 1),
            ("{%int(-1)}", -1),
            ("{%int(   -1   )}", -1),
            ("{%int(0001)}", 1),
            ("{%int(  0001   )}", 1),
        ],
    )
    def test_integer(self, integer: str, expected_integer: int):
        assert Script({"integer": integer}).resolve() == {"integer": Integer(expected_integer)}

    @pytest.mark.parametrize(
        "integer",
        [
            "{%add(0, --1)}",
            "{%add(0,  1-  )}",
            "{%add(0,-1-)}",
            "{%add(0,   -1 -   )}",
            "{%add(0,0001a)}",
            "{%add(0,  0001b   )}",
        ],
    )
    def test_invalid_integer(self, integer: str):
        with pytest.raises(InvalidSyntaxException, match=re.escape(str(NUMERICS_INVALID_CHAR))):
            Script({"integer": integer}).resolve()