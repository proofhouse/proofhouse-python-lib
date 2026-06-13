# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""The generated token strategy stays faithful to what the lexer emits."""

from hypothesis import given

from proofhouse_python_lib.lexer import tokenize
from proofhouse_python_lib.testing.strategies import tokens
from proofhouse_python_lib.tokens import Token


@given(tokens())
def test_generated_token_lexes_back_to_its_own_kind(token: Token) -> None:
    # A token the strategy hands out has to match one the lexer could
    # itself produce. Lexing its lexeme in isolation must yield exactly
    # one token carrying the same kind, which fails the moment the
    # strategy pairs a kind with a lexeme the lexer reads differently.
    lexed = tokenize(token.lexeme)
    assert lexed == (Token(token.kind, token.lexeme, 0),)
