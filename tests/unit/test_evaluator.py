# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Tests for the exact-arithmetic evaluator."""

from fractions import Fraction

import pytest

from proofhouse_python_lib.ast import (
    BinaryOp,
    BinaryOperator,
    Number,
    UnaryOp,
    UnaryOperator,
)
from proofhouse_python_lib.errors import DivisionByZeroError, ExpressionError
from proofhouse_python_lib.evaluator import evaluate, evaluate_text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("7", Fraction(7), id="number-lifts-to-fraction"),
        pytest.param("2+3", Fraction(5), id="addition"),
        pytest.param("10-4", Fraction(6), id="subtraction"),
        pytest.param("6*7", Fraction(42), id="multiplication"),
        pytest.param("8/2", Fraction(4), id="exact-division"),
        pytest.param("1/3", Fraction(1, 3), id="fraction-stays-exact"),
        pytest.param("2/6", Fraction(1, 3), id="fraction-reduces"),
        pytest.param("1/3+1/3+1/3", Fraction(1), id="thirds-sum-to-one"),
        pytest.param("1+2*3", Fraction(7), id="star-binds-tighter-than-plus"),
        pytest.param("(1+2)*3", Fraction(9), id="parens-override-precedence"),
        pytest.param("8-4/2", Fraction(6), id="slash-binds-tighter-than-minus"),
        pytest.param("9-5-2", Fraction(2), id="subtraction-left-associative"),
        pytest.param("8/4/2", Fraction(1), id="division-left-associative"),
        pytest.param("-3", Fraction(-3), id="unary-minus"),
        pytest.param("- -3", Fraction(3), id="unary-chain-cancels"),
        pytest.param("---3", Fraction(-3), id="triple-unary-chain"),
        pytest.param("-(1+2)", Fraction(-3), id="unary-over-group"),
        pytest.param("2*-3", Fraction(-6), id="unary-after-star"),
    ],
)
def test_evaluate_text_yields_exact_value(text: str, expected: Fraction) -> None:
    assert evaluate_text(text) == expected


def test_evaluate_walks_a_prebuilt_tree() -> None:
    tree = BinaryOp(
        BinaryOperator.MUL,
        UnaryOp(UnaryOperator.NEG, Number(4)),
        Number(5),
    )
    assert evaluate(tree) == Fraction(-20)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("1/0", id="literal-zero-divisor"),
        pytest.param("1/(2-2)", id="divisor-evaluates-to-zero"),
        pytest.param("0/0", id="zero-over-zero"),
    ],
)
def test_evaluate_text_rejects_zero_divisor(text: str) -> None:
    with pytest.raises(DivisionByZeroError, match="division by zero"):
        evaluate_text(text)


def test_division_by_zero_error_is_an_expression_error() -> None:
    with pytest.raises(ExpressionError):
        evaluate_text("5/0")
