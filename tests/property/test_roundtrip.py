# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Round-trip and idempotence properties tying parse and format together."""

from hypothesis import given

from proofhouse_python_lib.ast import Expr
from proofhouse_python_lib.formatter import format_expr
from proofhouse_python_lib.parser import parse
from proofhouse_python_lib.testing.strategies import expression_texts, expressions


@given(expressions())
def test_format_then_parse_recovers_the_tree(expr: Expr) -> None:
    # The canonical text a tree formats to must parse back to that same
    # tree. `format_expr` exists to keep exactly this contract, checked
    # here against shapes a hand-written table would never think to try.
    assert parse(format_expr(expr)) == expr


@given(expression_texts())
def test_format_of_parse_is_idempotent(text: str) -> None:
    # Formatting a parsed string yields the canonical spelling, and a
    # second round of parse-then-format must leave that spelling alone. A
    # later pass that altered anything would expose the first result as
    # something short of canonical.
    once = format_expr(parse(text))
    twice = format_expr(parse(once))
    assert once == twice
