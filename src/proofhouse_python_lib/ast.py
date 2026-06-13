# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""AST node types the parser produces."""

from dataclasses import dataclass
from enum import Enum, auto

# The trailing marker tells cosmic-ray to leave this line alone. A
# 695-style alias defers its body, so the union arms only ever feed a
# type checker and never run unless code reaches for `Expr.__value__`,
# which nothing does. Rewriting the `|` to any other operator changes no
# behavior a test could catch, so the sweep would otherwise log two dozen
# of these dead mutants nightly.
type Expr = Number | UnaryOp | BinaryOp  # pragma: no mutate


class UnaryOperator(Enum):
    """Operator a UnaryOp node applies to its operand."""

    NEG = auto()


class BinaryOperator(Enum):
    """Operator a BinaryOp node applies to its operands."""

    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()


@dataclass(frozen=True, slots=True)
class Number:
    """Integer literal leaf."""

    value: int


@dataclass(frozen=True, slots=True)
class UnaryOp:
    """Prefix operator applied to a single operand."""

    op: UnaryOperator
    operand: Expr


@dataclass(frozen=True, slots=True)
class BinaryOp:
    """Infix operator applied to a left and right operand."""

    op: BinaryOperator
    left: Expr
    right: Expr
