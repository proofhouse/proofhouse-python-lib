# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Lexer turning expression text into a token stream."""

import re
from typing import Final

from proofhouse_python_lib.errors import LexError
from proofhouse_python_lib.tokens import Token, TokenKind

_NUMBER: Final = re.compile(r"[0-9]+")

_SINGLE_CHAR_KINDS: Final[dict[str, TokenKind]] = {
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "*": TokenKind.STAR,
    "/": TokenKind.SLASH,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
}


def tokenize(text: str) -> tuple[Token, ...]:
    """Split expression text into tokens, raising LexError on stray characters."""
    tokens: list[Token] = []
    offset = 0
    while offset < len(text):
        char = text[offset]
        if char.isspace():
            offset += 1
        elif (match := _NUMBER.match(text, offset)) is not None:
            tokens.append(Token(TokenKind.NUMBER, match.group(), offset))
            offset = match.end()
        elif (kind := _SINGLE_CHAR_KINDS.get(char)) is not None:
            tokens.append(Token(kind, char, offset))
            offset += 1
        else:
            raise LexError(char, offset)
    return tuple(tokens)
