# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""AST node types the parser produces."""

from dataclasses import dataclass
from enum import Enum, auto

type Expr = Number | UnaryOp | BinaryOp


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
