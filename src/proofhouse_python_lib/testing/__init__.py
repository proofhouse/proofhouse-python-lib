# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Test helpers shipped as public API for downstream test suites."""

from proofhouse_python_lib.lexer import tokenize
from proofhouse_python_lib.tokens import TokenKind


def kinds(text: str) -> tuple[TokenKind, ...]:
    """Lex text and project each token down to its kind.

    Assertions that only care about the kind sequence read better
    against this projection than against full Token tuples.
    """
    return tuple(token.kind for token in tokenize(text))
