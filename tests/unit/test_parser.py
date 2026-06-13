# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Tests for the expression parser."""

import pytest

from proofhouse_python_lib.ast import (
    BinaryOp,
    BinaryOperator,
    Expr,
    Number,
    UnaryOp,
    UnaryOperator,
)
from proofhouse_python_lib.errors import ExpressionError, ParseError
from proofhouse_python_lib.formatter import binary_symbol
from proofhouse_python_lib.parser import parse


def render(expr: Expr) -> str:
    """Render an AST fully parenthesized, so its shape shows in one string.

    Unlike the library's canonical `format_expr`, every operator node
    wears parentheses here, so precedence and associativity read straight
    off the assertion string instead of hiding in whatever the
    minimal-parens form chose to drop.
    """
    match expr:
        case Number(value):
            return str(value)
        case UnaryOp(_, operand):
            return f"(-{render(operand)})"
        case BinaryOp(op, left, right):
            return f"({render(left)} {binary_symbol(op)} {render(right)})"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("7", Number(7), id="number"),
        pytest.param(
            "1+2",
            BinaryOp(BinaryOperator.ADD, Number(1), Number(2)),
            id="addition",
        ),
        pytest.param(
            "-3",
            UnaryOp(UnaryOperator.NEG, Number(3)),
            id="unary-minus",
        ),
        pytest.param("(7)", Number(7), id="parens-leave-no-node"),
    ],
)
def test_parse_builds_expected_nodes(text: str, expected: Expr) -> None:
    assert parse(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("1+2*3", "(1 + (2 * 3))", id="star-binds-tighter-than-plus"),
        pytest.param("1*2+3", "((1 * 2) + 3)", id="plus-after-star"),
        pytest.param("8-4/2", "(8 - (4 / 2))", id="slash-binds-tighter-than-minus"),
        pytest.param("1+2+3", "((1 + 2) + 3)", id="plus-left-associative"),
        pytest.param("9-5-2", "((9 - 5) - 2)", id="minus-left-associative"),
        pytest.param("8/4/2", "((8 / 4) / 2)", id="slash-left-associative"),
        pytest.param("2*3*4", "((2 * 3) * 4)", id="star-left-associative"),
        pytest.param("(1+2)*3", "((1 + 2) * 3)", id="parens-override-precedence"),
        pytest.param("2*(3-(4+5))", "(2 * (3 - (4 + 5)))", id="nested-parens"),
        pytest.param("((7))", "7", id="redundant-parens"),
        pytest.param("- -3", "(-(-3))", id="unary-chain"),
        pytest.param("---3", "(-(-(-3)))", id="triple-unary-chain"),
        pytest.param("-2*3", "((-2) * 3)", id="unary-binds-tighter-than-star"),
        pytest.param("2*-3", "(2 * (-3))", id="unary-after-star"),
        pytest.param("-(1+2)", "(-(1 + 2))", id="unary-over-group"),
        pytest.param(" 1 + 2 ", "(1 + 2)", id="whitespace-ignored"),
    ],
)
def test_parse_shapes_precedence_and_associativity(text: str, expected: str) -> None:
    assert render(parse(text)) == expected


@pytest.mark.parametrize(
    ("text", "message", "offset"),
    [
        pytest.param(
            "",
            "expected an operand, found end of input at offset 0",
            0,
            id="empty-input",
        ),
        pytest.param(
            "1+",
            "expected an operand, found end of input at offset 2",
            2,
            id="dangling-operator",
        ),
        pytest.param(
            "*3",
            "expected an operand, found '*' at offset 0",
            0,
            id="operator-at-start",
        ),
        pytest.param(
            "1+*2",
            "expected an operand, found '*' at offset 2",
            2,
            id="operator-after-operator",
        ),
        pytest.param(
            "()",
            "expected an operand, found ')' at offset 1",
            1,
            id="empty-group",
        ),
        pytest.param(
            "-",
            "expected an operand, found end of input at offset 1",
            1,
            id="bare-minus",
        ),
        pytest.param(
            "(1+2",
            "expected ')', found end of input at offset 4",
            4,
            id="unclosed-paren",
        ),
        pytest.param(
            "(1 2",
            "expected ')', found '2' at offset 3",
            3,
            id="operand-where-paren-closes",
        ),
        pytest.param(
            "1+2)",
            "expected end of input, found ')' at offset 3",
            3,
            id="unmatched-closing-paren",
        ),
        pytest.param(
            "1 2",
            "expected end of input, found '2' at offset 2",
            2,
            id="trailing-operand",
        ),
    ],
)
def test_parse_rejects_bad_syntax_with_offset(
    text: str, message: str, offset: int
) -> None:
    with pytest.raises(ParseError) as excinfo:
        parse(text)
    assert str(excinfo.value) == message
    assert excinfo.value.offset == offset


def test_parse_error_is_an_expression_error() -> None:
    with pytest.raises(ExpressionError):
        parse("(")
