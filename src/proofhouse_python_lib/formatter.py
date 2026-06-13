# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Render an expression AST back to its canonical source form."""

from typing import Final

from proofhouse_python_lib.ast import (
    BinaryOp,
    BinaryOperator,
    Expr,
    Number,
    UnaryOp,
    UnaryOperator,
)

_BINARY_SYMBOLS: Final[dict[BinaryOperator, str]] = {
    BinaryOperator.ADD: "+",
    BinaryOperator.SUB: "-",
    BinaryOperator.MUL: "*",
    BinaryOperator.DIV: "/",
}

_UNARY_SYMBOLS: Final[dict[UnaryOperator, str]] = {
    UnaryOperator.NEG: "-",
}


def binary_symbol(op: BinaryOperator) -> str:
    """Return the source character a binary operator lexes from.

    One mapping owns how an operator spells out, so nothing downstream
    keeps a second copy that could drift out of step with this one.
    """
    return _BINARY_SYMBOLS[op]


# Binding power of each node, on the grammar's own scale: additive
# operators sit lowest, multiplicative ones a step up, a prefix minus
# higher than those, and a bare value never needs guarding at all.
# Bracketing keys off these numbers alone, so the canonical text
# re-parses to the tree it came from.
_ADDITIVE: Final = 1
_MULTIPLICATIVE: Final = 2
_UNARY: Final = 3
_ATOM: Final = 4


def format_expr(expr: Expr) -> str:
    """Render an AST to canonical text that parses back to an equal tree.

    Binary operators take a single space on each side and a prefix minus
    none after it. Parentheses appear only where dropping them would let
    a looser operator below capture an operand, or let a left-associative
    chain re-bracket. Everywhere else the text stays bare.
    """
    match expr:
        case Number(value):
            return str(value)
        case UnaryOp(op, operand):
            return f"{_UNARY_SYMBOLS[op]}{_format_child(operand, _UNARY)}"
        case BinaryOp(op, left, right):
            precedence = _precedence(expr)
            # A left operand of equal power needs no guard, but a right
            # one does: left association means 9 - 5 - 2 brackets as
            # (9 - 5) - 2, so a same-power node on the right has to wear
            # parentheses to keep its own shape.
            rendered_left = _format_child(left, precedence)
            rendered_right = _format_child(right, precedence + 1)
            return f"{rendered_left} {binary_symbol(op)} {rendered_right}"


def _format_child(child: Expr, min_precedence: int) -> str:
    text = format_expr(child)
    if _precedence(child) < min_precedence:
        return f"({text})"
    return text


def _precedence(expr: Expr) -> int:
    match expr:
        case Number():
            return _ATOM
        case UnaryOp():
            return _UNARY
        case BinaryOp(op):
            if op in (BinaryOperator.MUL, BinaryOperator.DIV):
                return _MULTIPLICATIVE
            return _ADDITIVE
