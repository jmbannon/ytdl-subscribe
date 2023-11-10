import copy
import functools
import inspect
from abc import ABC
from dataclasses import dataclass
from inspect import FullArgSpec
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Type
from typing import Union
from typing import get_origin

from ytdl_sub.script.functions import Functions
from ytdl_sub.script.types.resolvable import ArgumentType
from ytdl_sub.script.types.resolvable import Resolvable
from ytdl_sub.script.types.resolvable import Resolvable_0
from ytdl_sub.script.types.resolvable import Resolvable_1
from ytdl_sub.script.types.resolvable import Resolvable_2
from ytdl_sub.script.types.variable import FunctionArgument
from ytdl_sub.script.types.variable import Variable
from ytdl_sub.script.types.variable_dependency import VariableDependency
from ytdl_sub.utils.exceptions import StringFormattingException


def is_union(arg_type: Type) -> bool:
    return get_origin(arg_type) is Union


@dataclass(frozen=True)
class FunctionInputSpec:
    args: Optional[List[Type[Resolvable | Optional[Resolvable]]]] = None
    varargs: Optional[Type[Resolvable]] = None

    def __post_init__(self):
        assert (self.args is None) ^ (self.varargs is None)

    @classmethod
    def _is_type_compatible(
        cls,
        input_arg: ArgumentType,
        expected_arg_type: Type[Resolvable | Optional[Resolvable]],
    ) -> bool:
        if isinstance(input_arg, Function):
            input_arg_type = input_arg.output_type
        elif isinstance(input_arg, Variable):
            return True  # unresolved variables can be anything, so pass for now
        else:
            input_arg_type = input_arg.__class__

        if is_union(expected_arg_type):
            # See if the arg is a valid against the union
            valid_type = False

            # if the input arg is a union, do a direct comparison
            if is_union(input_arg_type):
                valid_type = input_arg_type == expected_arg_type
            # otherwise, iterate the union to see if it's compatible
            else:
                for union_type in expected_arg_type.__args__:
                    if issubclass(input_arg_type, union_type):
                        valid_type = True
                        break

            if not valid_type:
                return False
        # If the input is a union and the expected type is not, see if
        # each possible union input is compatible with the expected type
        elif is_union(input_arg_type):
            for union_type in input_arg_type.__args__:
                if not issubclass(union_type, expected_arg_type):
                    return False

        elif not issubclass(input_arg_type, expected_arg_type):
            return False

        return True

    def _is_args_compatible(self, input_args: List[ArgumentType]) -> bool:
        assert self.args is not None

        if len(input_args) > len(self.args):
            return False

        for idx in range(len(self.args)):
            input_arg = input_args[idx] if idx < len(input_args) else None
            if not self._is_type_compatible(input_arg=input_arg, expected_arg_type=self.args[idx]):
                return False

        return True

    def _is_varargs_compatible(self, input_args: List[ArgumentType]) -> bool:
        assert self.varargs is not None

        for input_arg in input_args:
            if not self._is_type_compatible(input_arg=input_arg, expected_arg_type=self.varargs):
                return False

        return True

    def is_compatible(self, input_args: List[ArgumentType]) -> bool:
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
class Function(VariableDependency, ArgumentType, ABC):
    name: str
    args: List[ArgumentType]

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
            elif isinstance(arg, VariableDependency):
                variables.update(arg.variables)

        return variables

    @property
    def function_arguments(self) -> Set[FunctionArgument]:
        """
        Returns
        -------
        All function arguments used within the function
        """
        function_arguments: Set[FunctionArgument] = set()
        for arg in self.args:
            if isinstance(arg, FunctionArgument):
                function_arguments.add(arg)
            elif isinstance(arg, VariableDependency):
                function_arguments.update(arg.function_arguments)

        return function_arguments

    @classmethod
    def from_name_and_args(cls, name: str, args: List[ArgumentType]) -> "Function":
        if hasattr(Functions, name) or hasattr(Functions, name + "_"):
            return BuiltInFunction(name=name, args=args)

        return CustomFunction(name=name, args=args)


class CustomFunction(Function):
    def resolve(
        self,
        resolved_variables: Dict[Variable, Resolvable],
        custom_functions: Dict[str, "VariableDependency"],
    ) -> Resolvable:
        resolved_args: List[Resolvable] = [
            self._resolve_argument_type(
                arg=arg, resolved_variables=resolved_variables, custom_functions=custom_functions
            )
            for arg in self.args
        ]

        if self.name in custom_functions:
            if len(self.args) != len(custom_functions[self.name].function_arguments):
                raise StringFormattingException("Custom function arg length does not equal")

            resolved_variables_with_args = copy.deepcopy(resolved_variables)
            for i, arg in enumerate(resolved_args):
                function_arg = FunctionArgument(name=f"${i+1}")  # Function args are 1-based
                if function_arg in resolved_variables_with_args:
                    raise StringFormattingException("nested custom functions???")
                resolved_variables_with_args[function_arg] = arg

            return custom_functions[self.name].resolve(
                resolved_variables=resolved_variables_with_args,
                custom_functions=custom_functions,
            )
        else:
            raise StringFormattingException(f"Custom function {self.name} does not exist")


class BuiltInFunction(Function):
    def _expected_received_error_msg(self) -> str:
        received_type_names: List[str] = []
        for arg in self.args:
            if isinstance(arg, BuiltInFunction):
                received_type_names.append(f"%{arg.name}(...)->{arg.output_type.__name__}")
            else:
                received_type_names.append(arg.__class__.__name__)

        received_args_str = f"({', '.join([name for name in received_type_names])})"

        return f"Expected {self.input_spec.expected_args_str()}.\nReceived {received_args_str}"

    def __post_init__(self):
        if not self.input_spec.is_compatible(input_args=self.args):
            raise StringFormattingException(
                f"Invalid arguments passed to function {self.name}.\n"
                f"{self._expected_received_error_msg()}"
            )

    @property
    def callable(self) -> Callable[..., Resolvable]:
        if hasattr(Functions, self.name):
            return getattr(Functions, self.name)
        if hasattr(Functions, self.name + "_"):
            return getattr(Functions, self.name + "_")

        raise StringFormattingException(f"Function name {self.name} does not exist")

    @functools.cached_property
    def arg_spec(self) -> FullArgSpec:
        return inspect.getfullargspec(self.callable)

    @property
    def input_spec(self) -> FunctionInputSpec:
        return FunctionInputSpec.from_function(self)

    @property
    def output_type(self) -> Type[Resolvable]:
        output_type = self.arg_spec.annotations["return"]
        if is_union(output_type):
            union_types_list = []
            for union_type in output_type.__args__:
                if union_type == Resolvable_0:
                    union_types_list.append(type(self.args[0]))
                elif union_type == Resolvable_1:
                    union_types_list.append(type(self.args[1]))
                elif union_type == Resolvable_2:
                    union_types_list.append(type(self.args[2]))
                else:
                    union_types_list.append(union_type)

            return Union[tuple(union_types_list)]

        return output_type

    def resolve(
        self,
        resolved_variables: Dict[Variable, Resolvable],
        custom_functions: Dict[str, "VariableDependency"],
    ) -> Resolvable:
        resolved_args: List[Resolvable] = [
            self._resolve_argument_type(
                arg=arg, resolved_variables=resolved_variables, custom_functions=custom_functions
            )
            for arg in self.args
        ]

        return self.callable(*resolved_args)
