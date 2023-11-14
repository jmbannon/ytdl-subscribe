import re
from typing import Tuple

import pytest

from ytdl_sub.script.parser import NUMERICS_INVALID_CHAR, STRINGS_ONLY_ARGS
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


class TestFunction:
    pass