# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Totality of the evaluator over arbitrary well-formed trees."""

from fractions import Fraction

from hypothesis import given

from proofhouse_python_lib.ast import BinaryOp, BinaryOperator, Expr, Number, UnaryOp
from proofhouse_python_lib.errors import DivisionByZeroError
from proofhouse_python_lib.evaluator import evaluate
from proofhouse_python_lib.testing.strategies import expressions


def _has_division(expr: Expr) -> bool:
    """Report whether any node under `expr` carries a division."""
    match expr:
        case Number():
            return False
        case UnaryOp(_, operand):
            return _has_division(operand)
        case BinaryOp(BinaryOperator.DIV):
            return True
        case BinaryOp(_, left, right):
            return _has_division(left) or _has_division(right)


@given(expressions())
def test_evaluate_returns_a_fraction_or_rejects_a_zero_divisor(expr: Expr) -> None:
    # The evaluator stays total over well-formed trees. Every input
    # either reduces to a `Fraction` or raises `DivisionByZeroError`,
    # with nothing else allowed to escape. A stray `TypeError` would slip
    # past the `except` below and trip the final assertion instead.
    try:
        result = evaluate(expr)
    except DivisionByZeroError:
        return
    assert isinstance(result, Fraction)


@given(expressions())
def test_division_free_trees_always_evaluate(expr: Expr) -> None:
    # A zero divisor gives the evaluator its one reason to raise, so a
    # tree holding no division at all can't raise for any reason. This
    # pins the "only when a zero divisor exists" half of totality, and it
    # never re-derives the value the evaluator already computes.
    if _has_division(expr):
        return
    assert isinstance(evaluate(expr), Fraction)
