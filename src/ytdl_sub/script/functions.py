from abc import ABC
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

T = TypeVar("T")
NumericT = TypeVar("NumericT", bound=int | float)


@dataclass(frozen=True)
class Resolvable(ABC, Generic[T]):
    value: T

    def resolve(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Numeric(Resolvable[NumericT], ABC, Generic[NumericT]):
    pass


@dataclass(frozen=True)
class Integer(Resolvable[int]):
    pass


@dataclass(frozen=True)
class Float(Resolvable[float]):
    pass


@dataclass(frozen=True)
class Boolean(Resolvable[bool]):
    pass


@dataclass(frozen=True)
class String(Resolvable[str]):
    pass


class StringFunctions:
    @staticmethod
    def lower(string: String) -> String:
        """
        Returns
        -------
        Lower-cased string
        """
        return String(string.value.lower())

    @staticmethod
    def upper(string: String) -> String:
        """
        Returns
        -------
        Upper-cased string
        """
        return String(string.value.upper())

    @staticmethod
    def capitalize(string: String) -> String:
        """
        Returns
        -------
        Capitalized string
        """
        return String(string.value.capitalize())

    @staticmethod
    def concat(l_string: String, r_string: String) -> String:
        return String(f"{l_string}{r_string}")


class Functions(StringFunctions):
    pass
