# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Parser turning expression text into an AST."""

from typing import Final

from proofhouse_python_lib.ast import (
    BinaryOp,
    BinaryOperator,
    Expr,
    Number,
    UnaryOp,
    UnaryOperator,
)
from proofhouse_python_lib.errors import ParseError
from proofhouse_python_lib.lexer import tokenize
from proofhouse_python_lib.tokens import Token, TokenKind

# Descriptions ParseError stitches into its "expected X, found Y"
# message. Naming them keeps one spelling per production across the
# raise sites.
_OPERAND: Final = "an operand"
_CLOSING_PAREN: Final = "')'"
_END_OF_INPUT: Final = "end of input"

_BINARY_OPERATORS: Final[dict[TokenKind, tuple[BinaryOperator, int]]] = {
    TokenKind.PLUS: (BinaryOperator.ADD, 1),
    TokenKind.MINUS: (BinaryOperator.SUB, 1),
    TokenKind.STAR: (BinaryOperator.MUL, 2),
    TokenKind.SLASH: (BinaryOperator.DIV, 2),
}


def parse(text: str) -> Expr:
    """Parse expression text into an AST, raising ParseError on bad syntax."""
    parser = _Parser(tokenize(text), end_offset=len(text))
    expr = parser.parse_expression(min_precedence=1)
    parser.check_exhausted()
    return expr


class _Parser:
    """Precedence-climbing parser over a fixed token stream."""

    def __init__(self, tokens: tuple[Token, ...], end_offset: int) -> None:
        self._tokens = tokens
        self._position = 0
        self._end_offset = end_offset

    def parse_expression(self, min_precedence: int) -> Expr:
        """Parse binary chains whose operators bind at least as tightly as given."""
        left = self._parse_operand()
        while (operator := self._peek_binary_operator()) is not None:
            op, precedence = operator
            if precedence < min_precedence:
                break
            self._position += 1
            right = self.parse_expression(min_precedence=precedence + 1)
            left = BinaryOp(op, left, right)
        return left

    def check_exhausted(self) -> None:
        """Raise ParseError if any token follows the parsed expression."""
        if self._position < len(self._tokens):
            token = self._tokens[self._position]
            raise ParseError(_END_OF_INPUT, repr(token.lexeme), token.offset)

    def _parse_operand(self) -> Expr:
        token = self._take(_OPERAND)
        if token.kind is TokenKind.NUMBER:
            return Number(int(token.lexeme))
        if token.kind is TokenKind.MINUS:
            return UnaryOp(UnaryOperator.NEG, self._parse_operand())
        if token.kind is TokenKind.LPAREN:
            inner = self.parse_expression(min_precedence=1)
            closing = self._take(_CLOSING_PAREN)
            if closing.kind is not TokenKind.RPAREN:
                raise ParseError(_CLOSING_PAREN, repr(closing.lexeme), closing.offset)
            return inner
        raise ParseError(_OPERAND, repr(token.lexeme), token.offset)

    def _peek_binary_operator(self) -> tuple[BinaryOperator, int] | None:
        if self._position == len(self._tokens):
            return None
        return _BINARY_OPERATORS.get(self._tokens[self._position].kind)

    def _take(self, expected: str) -> Token:
        if self._position == len(self._tokens):
            raise ParseError(expected, _END_OF_INPUT, self._end_offset)
        token = self._tokens[self._position]
        self._position += 1
        return token
