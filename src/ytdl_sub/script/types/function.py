import functools
import inspect
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from inspect import FullArgSpec
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Type
from typing import Union
from typing import final
from typing import get_origin

from ytdl_sub.script.functions import Functions
from ytdl_sub.script.types.resolvable import Boolean
from ytdl_sub.script.types.resolvable import Float
from ytdl_sub.script.types.resolvable import Integer
from ytdl_sub.script.types.resolvable import Resolvable
from ytdl_sub.script.types.resolvable import String
from ytdl_sub.script.types.variable import Variable
from ytdl_sub.utils.exceptions import StringFormattingException

ArgumentType = Union[Integer, Float, String, Boolean, Variable, "Function"]


@dataclass(frozen=True)
class VariableDependency(ABC):
    @property
    @abstractmethod
    def variables(self) -> Set[Variable]:
        raise NotImplemented()

    @abstractmethod
    def resolve(self, resolved_variables: Dict[Variable, Resolvable]) -> str:
        raise NotImplemented()

    @final
    def has_variable_dependency(self, resolved_variables: Dict[Variable, Resolvable]) -> bool:
        """
        Returns
        -------
        True if variable dependency. False otherwise.
        """
        return self.variables.issubset(set(resolved_variables.keys()))


@dataclass(frozen=True)
class FunctionInputSpec:
    args: Optional[List[Type[Resolvable | Optional[Resolvable]]]] = None
    varargs: Optional[Type[Resolvable]] = None

    def __post_init__(self):
        assert (self.args is None) ^ (self.varargs is None)

    @classmethod
    def _is_type_compatible(
        cls,
        input_arg: Optional[Resolvable],
        expected_arg_type: Type[Resolvable | Optional[Resolvable]],
    ) -> bool:
        input_arg_type = input_arg.__class__

        if get_origin(expected_arg_type) is Union:
            if input_arg_type not in expected_arg_type.__args__:
                return False
        elif input_arg_type != expected_arg_type:
            return False

        return True

    def _is_args_compatible(self, input_args: List[Resolvable | Optional[Resolvable]]) -> bool:
        assert self.args is not None

        if len(input_args) > len(self.args):
            return False

        for idx in range(len(self.args)):
            input_arg = input_args[idx] if idx < len(input_args) else None
            if not self._is_type_compatible(input_arg=input_arg, expected_arg_type=self.args[idx]):
                return False

        return True

    def _is_varargs_compatible(self, input_args: List[Resolvable | Optional[Resolvable]]) -> bool:
        assert self.varargs is not None

        for input_arg in input_args:
            if not self._is_type_compatible(input_arg=input_arg, expected_arg_type=self.varargs):
                return False

        return True

    def is_compatible(self, input_args: List[Resolvable | Optional[Resolvable]]) -> bool:
        if self.args is not None:
            return self._is_args_compatible(input_args=input_args)
        elif self.varargs is not None:
            return self._is_varargs_compatible(input_args=input_args)
        else:
            assert False, "should never reach here"

    def expected_args_str(self) -> str:
        if self.args is not None:
            return f"({', '.join([type_.__name__ for type_ in self.args])})"
        elif self.varargs is not None:
            return f"({self.varargs.__name__}, ...)"

    @classmethod
    def from_function(cls, func: "Function") -> "FunctionInputSpec":
        if func.arg_spec.varargs:
            return FunctionInputSpec(varargs=func.arg_spec.annotations[func.arg_spec.varargs])

        return FunctionInputSpec(
            args=[func.arg_spec.annotations[arg_name] for arg_name in func.arg_spec.args]
        )


@dataclass(frozen=True)
class Function(VariableDependency):
    name: str
    args: List[ArgumentType]

    def __post_init__(self):
        if not self.input_spec.is_compatible(input_args=self.args):
            raise StringFormattingException(
                f"Invalid arguments passed to function {self.name}.\n"
                f"{self._expected_received_error_msg()}"
            )

    def _expected_received_error_msg(self) -> str:
        received_type_names: List[str] = []
        for arg in self.args:
            if isinstance(arg, Function):
                received_type_names.append(f"%{arg.name}(...)->{arg.output_type.__name__}")
            else:
                received_type_names.append(arg.__class__.__name__)

        received_args_str = f"({', '.join([name for name in received_type_names])})"

        return f"Expected {self.input_spec.expected_args_str()}.\nReceived {received_args_str}"

    @property
    def callable(self) -> Callable[..., Resolvable]:
        try:
            return getattr(Functions, self.name)
        except AttributeError:
            raise StringFormattingException(f"Function name {self.name} does not exist")

    @functools.cached_property
    def arg_spec(self) -> FullArgSpec:
        return inspect.getfullargspec(self.callable)

    @property
    def input_spec(self) -> FunctionInputSpec:
        return FunctionInputSpec.from_function(self)

    @property
    def output_type(self) -> Type[Resolvable]:
        return self.arg_spec.annotations["return"]

    @property
    def variables(self) -> Set[Variable]:
        """
        Returns
        -------
        All variables used within the function
        """
        variables: Set[Variable] = set()
        for arg in self.args:
            if isinstance(arg, Variable):
                variables.add(arg)
            elif isinstance(arg, Function):
                variables.update(arg.variables)

        return variables

    def resolve(self, resolved_variables: Dict[Variable, Resolvable]) -> Resolvable:
        raise NotImplemented()
