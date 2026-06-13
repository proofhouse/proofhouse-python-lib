# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Hypothesis strategies that generate the engine's own data shapes.

These ship in the wheel for downstream property suites the way the
rest of `testing` does, but they lean on hypothesis, which the library
itself never imports. Anyone driving these strategies brings hypothesis
in through their own test dependencies; importing the package at runtime
stays free of it because only this submodule reaches for it.
"""

from typing import Final

from hypothesis import strategies as st

from proofhouse_python_lib.ast import (
    BinaryOp,
    BinaryOperator,
    Expr,
    Number,
    UnaryOp,
    UnaryOperator,
)
from proofhouse_python_lib.formatter import format_expr
from proofhouse_python_lib.tokens import Token, TokenKind

# The lexeme each single-character token kind always carries. `NUMBER`
# stays out of this table on purpose, because its lexeme spans a run of
# digits that the strategy draws separately. Keeping it apart stops a
# generated token from pairing a kind with text the lexer would read
# some other way.
_OPERATOR_LEXEMES: Final[dict[TokenKind, str]] = {
    TokenKind.PLUS: "+",
    TokenKind.MINUS: "-",
    TokenKind.STAR: "*",
    TokenKind.SLASH: "/",
    TokenKind.LPAREN: "(",
    TokenKind.RPAREN: ")",
}


@st.composite
def tokens(draw: st.DrawFn) -> Token:
    """Generate one well-formed `Token`.

    Each token pairs a kind with a lexeme the lexer could have emitted for
    it. A `NUMBER` draws a digit run; every operator and bracket takes its
    one fixed character. Offsets range over the nonnegative integers,
    since a token on its own says nothing about where its neighbors sit.
    """
    kind = draw(st.sampled_from(TokenKind))
    offset = draw(st.integers(min_value=0))
    if kind is TokenKind.NUMBER:
        lexeme = str(draw(st.integers(min_value=0)))
    else:
        lexeme = _OPERATOR_LEXEMES[kind]
    return Token(kind, lexeme, offset)


def expressions(max_depth: int = 4) -> st.SearchStrategy[Expr]:
    """Build well-formed `Expr` trees up to a bounded nesting depth.

    A leaf holds a `Number` over a nonnegative literal, matching the lexer,
    which only ever produces nonnegative integers. Negative values then
    arrive the way a parsed tree carries them, wrapped in a `UnaryOp`.
    Branches either apply that prefix minus to one child or join two
    children under a binary operator. `max_depth` caps how many nodes the
    recursion stacks before it bottoms out at a leaf.
    """
    numbers = st.builds(Number, st.integers(min_value=0))
    return st.recursive(numbers, _extend, max_leaves=max_depth)


def expression_texts(max_depth: int = 4) -> st.SearchStrategy[str]:
    """Derive source strings that parse back to a generated tree.

    Each string carries the canonical rendering of a tree from
    `expressions`, which keeps it parseable by construction. A suite draws
    arbitrary valid input straight from this strategy, rather than
    filtering a raw character strategy down to the rare string the grammar
    would accept.
    """
    return expressions(max_depth).map(format_expr)


def _extend(children: st.SearchStrategy[Expr]) -> st.SearchStrategy[Expr]:
    unary = st.builds(UnaryOp, st.just(UnaryOperator.NEG), children)
    binary = st.builds(BinaryOp, st.sampled_from(BinaryOperator), children, children)
    return st.one_of(unary, binary)
