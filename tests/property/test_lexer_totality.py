# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Totality of the lexer over arbitrary text, not just valid input."""

from hypothesis import given
from hypothesis import strategies as st

from proofhouse_python_lib.errors import LexError
from proofhouse_python_lib.lexer import tokenize
from proofhouse_python_lib.tokens import Token


@given(st.text())
def test_tokenize_either_lexes_or_raises_lex_error(text: str) -> None:
    # Handed any string at all, the lexer has exactly two outcomes: a
    # tuple of tokens, or a `LexError`. It returns no partial result and
    # walks off no end into an `IndexError`. The `text` strategy reaches
    # control characters and stray symbols a curated list would miss,
    # where an off-by-one in the scan would surface.
    try:
        result = tokenize(text)
    except LexError as error:
        offset = error.offset
    else:
        assert all(isinstance(token, Token) for token in result)
        return
    # The reported offset has to land inside the text it came from.
    assert 0 <= offset < len(text)


@given(st.text(alphabet="0123456789+-*/() \t"))
def test_tokenize_accepts_any_string_of_legal_characters(text: str) -> None:
    # Every character here can start a token, so no arrangement of them
    # can trip the error path: drawn only from the legal alphabet, the
    # lexer must always return a tuple.
    assert isinstance(tokenize(text), tuple)
