# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Tests for the canonical expression formatter."""

import pytest

from proofhouse_python_lib.ast import (
    BinaryOp,
    BinaryOperator,
    Expr,
    Number,
    UnaryOp,
    UnaryOperator,
)
from proofhouse_python_lib.formatter import format_expr
from proofhouse_python_lib.parser import parse


def _add(left: Expr, right: Expr) -> BinaryOp:
    return BinaryOp(BinaryOperator.ADD, left, right)


def _sub(left: Expr, right: Expr) -> BinaryOp:
    return BinaryOp(BinaryOperator.SUB, left, right)


def _mul(left: Expr, right: Expr) -> BinaryOp:
    return BinaryOp(BinaryOperator.MUL, left, right)


def _div(left: Expr, right: Expr) -> BinaryOp:
    return BinaryOp(BinaryOperator.DIV, left, right)


def _neg(operand: Expr) -> UnaryOp:
    return UnaryOp(UnaryOperator.NEG, operand)


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        pytest.param(Number(7), "7", id="bare-number"),
        pytest.param(_add(Number(1), Number(2)), "1 + 2", id="addition-spacing"),
        pytest.param(_div(Number(8), Number(2)), "8 / 2", id="division-spacing"),
        pytest.param(_neg(Number(3)), "-3", id="unary-minus-no-space"),
        pytest.param(_neg(_neg(Number(3))), "--3", id="unary-chain-stays-bare"),
        # A looser operator under a tighter one keeps its parentheses.
        pytest.param(
            _mul(_add(Number(1), Number(2)), Number(3)),
            "(1 + 2) * 3",
            id="sum-times-needs-parens",
        ),
        pytest.param(
            _neg(_add(Number(1), Number(2))), "-(1 + 2)", id="negate-sum-needs-parens"
        ),
        # A tighter operator under a looser one drops them.
        pytest.param(
            _add(Number(1), _mul(Number(2), Number(3))),
            "1 + 2 * 3",
            id="plus-over-product-bare",
        ),
        pytest.param(
            _mul(Number(2), _neg(Number(3))), "2 * -3", id="product-over-unary-bare"
        ),
        pytest.param(
            _mul(_neg(Number(3)), Number(5)), "-3 * 5", id="unary-left-of-product-bare"
        ),
        # Left association: a same-power left child stays bare, a
        # same-power right child takes parentheses.
        pytest.param(
            _sub(_sub(Number(9), Number(5)), Number(2)),
            "9 - 5 - 2",
            id="left-chain-bare",
        ),
        pytest.param(
            _sub(Number(9), _sub(Number(5), Number(2))),
            "9 - (5 - 2)",
            id="right-assoc-needs-parens",
        ),
        pytest.param(
            _div(_div(Number(8), Number(4)), Number(2)),
            "8 / 4 / 2",
            id="left-division-chain-bare",
        ),
        pytest.param(
            _div(Number(8), _div(Number(4), Number(2))),
            "8 / (4 / 2)",
            id="right-division-needs-parens",
        ),
    ],
)
def test_format_expr_canonical_form(expr: Expr, expected: str) -> None:
    assert format_expr(expr) == expected


@pytest.mark.parametrize(
    "expr",
    [
        pytest.param(Number(42), id="number"),
        pytest.param(_neg(_neg(Number(1))), id="double-unary"),
        pytest.param(
            _mul(_add(Number(1), Number(2)), _sub(Number(3), Number(4))),
            id="grouped-on-both-sides",
        ),
        pytest.param(
            _sub(Number(9), _sub(Number(5), Number(2))), id="right-nested-subtraction"
        ),
        pytest.param(
            _neg(_add(Number(1), _mul(Number(2), Number(3)))),
            id="negated-mixed-precedence",
        ),
        pytest.param(
            _div(_div(Number(8), Number(4)), Number(2)), id="left-division-chain"
        ),
    ],
)
def test_format_expr_roundtrips_through_parse(expr: Expr) -> None:
    assert parse(format_expr(expr)) == expr


def test_minimal_parens_keep_grouping_but_drop_redundancy() -> None:
    # (1+2)*3 must keep its parentheses; 1+(2*3) must shed them, since
    # the product already binds tighter than the sum around it.
    assert format_expr(_mul(_add(Number(1), Number(2)), Number(3))) == "(1 + 2) * 3"
    assert format_expr(_add(Number(1), _mul(Number(2), Number(3)))) == "1 + 2 * 3"
