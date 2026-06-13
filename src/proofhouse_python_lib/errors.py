# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Errors raised while processing expressions."""


class ExpressionError(Exception):
    """Base class for every expression-processing error this library raises."""


class LexError(ExpressionError):
    """Raised when the lexer meets a character that can't start a token."""

    def __init__(self, char: str, offset: int) -> None:
        super().__init__(f"unexpected character {char!r} at offset {offset}")
        self.offset: int = offset


class ParseError(ExpressionError):
    """Raised when the token stream doesn't form a valid expression."""

    def __init__(self, expected: str, found: str, offset: int) -> None:
        super().__init__(f"expected {expected}, found {found} at offset {offset}")
        self.offset: int = offset


class DivisionByZeroError(ExpressionError):
    """Raised when evaluation divides by a zero divisor.

    The AST carries no source positions, so this error carries none
    either: it names a structural fact about the tree, not a span of
    input text the way LexError and ParseError do.
    """

    def __init__(self) -> None:
        super().__init__("division by zero")
