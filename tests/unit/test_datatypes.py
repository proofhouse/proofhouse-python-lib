# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Tests for the value-type guarantees of AST nodes and tokens."""

import dataclasses

import pytest

from proofhouse_python_lib.ast import (
    BinaryOp,
    BinaryOperator,
    Number,
    UnaryOp,
    UnaryOperator,
)
from proofhouse_python_lib.tokens import Token, TokenKind

_NUMBER = Number(7)
_UNARY = UnaryOp(UnaryOperator.NEG, _NUMBER)
_BINARY = BinaryOp(BinaryOperator.ADD, _NUMBER, _NUMBER)
_TOKEN = Token(TokenKind.NUMBER, "7", 0)


@pytest.mark.parametrize(
    ("value", "field"),
    [
        pytest.param(_NUMBER, "value", id="number"),
        pytest.param(_UNARY, "operand", id="unary-op"),
        pytest.param(_BINARY, "left", id="binary-op"),
        pytest.param(_TOKEN, "offset", id="token"),
    ],
)
def test_value_types_reject_attribute_writes(value: object, field: str) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(value, field, _NUMBER)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(_NUMBER, id="number"),
        pytest.param(_UNARY, id="unary-op"),
        pytest.param(_BINARY, id="binary-op"),
        pytest.param(_TOKEN, id="token"),
    ],
)
def test_value_types_carry_slots_and_no_instance_dict(value: object) -> None:
    # A slotted instance owns no `__dict__`, so an unknown attribute has
    # nowhere to land. A misspelled field name then raises instead of
    # quietly becoming a new attribute.
    assert not hasattr(value, "__dict__")


def test_number_equality_and_hash_track_value() -> None:
    # Frozen plus slotted buys a usable `__hash__` and value equality,
    # the pair a downstream memo or set keys on.
    assert Number(5) == Number(5)
    assert Number(5) != Number(6)
    assert len({Number(5), Number(5), Number(6)}) == 2
