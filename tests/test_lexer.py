# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Tests for the expression lexer."""

import pytest

from proofhouse_python_lib.errors import ExpressionError, LexError
from proofhouse_python_lib.lexer import tokenize
from proofhouse_python_lib.tokens import Token, TokenKind


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(
            "7",
            (Token(TokenKind.NUMBER, "7", 0),),
            id="single-digit",
        ),
        pytest.param(
            "1234",
            (Token(TokenKind.NUMBER, "1234", 0),),
            id="multi-digit",
        ),
        pytest.param(
            "007",
            (Token(TokenKind.NUMBER, "007", 0),),
            id="leading-zeros",
        ),
        pytest.param(
            "1+2",
            (
                Token(TokenKind.NUMBER, "1", 0),
                Token(TokenKind.PLUS, "+", 1),
                Token(TokenKind.NUMBER, "2", 2),
            ),
            id="adjacent-tokens",
        ),
        pytest.param(
            "+-*/()",
            (
                Token(TokenKind.PLUS, "+", 0),
                Token(TokenKind.MINUS, "-", 1),
                Token(TokenKind.STAR, "*", 2),
                Token(TokenKind.SLASH, "/", 3),
                Token(TokenKind.LPAREN, "(", 4),
                Token(TokenKind.RPAREN, ")", 5),
            ),
            id="every-single-char-kind",
        ),
        pytest.param(
            " 12 * (34 - 5) / 6 ",
            (
                Token(TokenKind.NUMBER, "12", 1),
                Token(TokenKind.STAR, "*", 4),
                Token(TokenKind.LPAREN, "(", 6),
                Token(TokenKind.NUMBER, "34", 7),
                Token(TokenKind.MINUS, "-", 10),
                Token(TokenKind.NUMBER, "5", 12),
                Token(TokenKind.RPAREN, ")", 13),
                Token(TokenKind.SLASH, "/", 15),
                Token(TokenKind.NUMBER, "6", 17),
            ),
            id="whitespace-shifts-offsets",
        ),
    ],
)
def test_tokenize_yields_expected_tokens(
    text: str, expected: tuple[Token, ...]
) -> None:
    assert tokenize(text) == expected


@pytest.mark.parametrize("text", ["", " ", " \t\n  "], ids=["empty", "space", "mixed"])
def test_tokenize_empty_or_whitespace_input_yields_no_tokens(text: str) -> None:
    assert tokenize(text) == ()


@pytest.mark.parametrize(
    ("text", "char", "offset"),
    [
        pytest.param("a", "a", 0, id="letter-at-start"),
        pytest.param("12 $ 3", "$", 3, id="symbol-after-number"),
        pytest.param("1.5", ".", 1, id="decimal-point"),
    ],
)
def test_tokenize_rejects_stray_character_with_offset(
    text: str, char: str, offset: int
) -> None:
    with pytest.raises(LexError) as excinfo:
        tokenize(text)
    assert excinfo.value.offset == offset
    assert repr(char) in str(excinfo.value)


def test_lex_error_is_an_expression_error() -> None:
    with pytest.raises(ExpressionError):
        tokenize("?")
