# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Token kinds and the token record the lexer produces."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    """Classification of a lexed token."""

    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    LPAREN = auto()
    RPAREN = auto()


@dataclass(frozen=True, slots=True)
class Token:
    """One lexed token: its kind, source text, and offset into the input."""

    kind: TokenKind
    lexeme: str
    offset: int
