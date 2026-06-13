# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Exact-arithmetic evaluator walking an expression AST."""

from fractions import Fraction
from typing import assert_never

from proofhouse_python_lib.ast import (
    BinaryOp,
    BinaryOperator,
    Expr,
    Number,
    UnaryOp,
)
from proofhouse_python_lib.errors import DivisionByZeroError
from proofhouse_python_lib.parser import parse


def evaluate(expr: Expr) -> Fraction:
    """Reduce an AST to its exact rational value.

    Integer literals lift to Fraction so the whole computation stays
    in exact rationals, and division reduces rather than rounds. A zero
    divisor raises DivisionByZeroError.
    """
    match expr:
        case Number(value):
            return Fraction(value)
        case UnaryOp(_, operand):
            # Negation, the one prefix operator, always flips the sign.
            return -evaluate(operand)
        case BinaryOp(op, left, right):
            return _apply_binary(op, evaluate(left), evaluate(right))
        case _:
            assert_never(expr)


def evaluate_text(text: str) -> Fraction:
    """Parse expression text and reduce it to its exact rational value."""
    return evaluate(parse(text))


def _apply_binary(op: BinaryOperator, left: Fraction, right: Fraction) -> Fraction:
    match op:
        case BinaryOperator.ADD:
            return left + right
        case BinaryOperator.SUB:
            return left - right
        case BinaryOperator.MUL:
            return left * right
        case BinaryOperator.DIV:
            if right == 0:
                raise DivisionByZeroError
            return left / right
        case _:
            assert_never(op)
