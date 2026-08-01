# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Tests for the diff scoping behind the mutate-diff gate."""

import subprocess
from pathlib import Path

import pytest
from tools.mutscope import _changed_modules, semantics_match

MODULE_PATH = Path("src/proofhouse_python_lib/errors.py")

BASE = '''"""Errors the expression pipeline raises."""


class DivisionByZeroError(Exception):
    """Raised when evaluation divides by a zero divisor.

    The AST carries no source positions, so this error carries none
    either.
    """

    detail = "division by a zero divisor"

    def __init__(self) -> None:
        super().__init__(self.detail)
'''

# Prose reworded and nothing else moved, the shape of the edit that
# turned the gate red.
DOCSTRING_REWORD = BASE.replace(
    "The AST carries no source positions, so this error carries none\n    either.",
    "The AST carries no source positions, so this error carries none\n    of its own.",
)

# A comment never becomes a node in the tree, so this reads as prose too.
COMMENT_ONLY = BASE.replace(
    "    def __init__(self) -> None:",
    "    # The message needs no argument.\n    def __init__(self) -> None:",
)

CODE_CHANGE = BASE.replace(
    "super().__init__(self.detail)",
    "super().__init__(self.detail.upper())",
)

# A docstring riding into the same hunk as a real edit must not shield it.
MIXED = DOCSTRING_REWORD.replace(
    "super().__init__(self.detail)",
    "super().__init__(self.detail.upper())",
)

# A class-level string that no reader treats as a docstring. The message
# text carries into whatever catches the error, so a mutant can move it.
STRING_VALUE = BASE.replace(
    'detail = "division by a zero divisor"',
    'detail = "division by zero"',
)

BROKEN_SYNTAX = BASE.replace("class DivisionByZeroError(Exception):", "class ???:")


@pytest.mark.parametrize(
    ("after", "expected"),
    [
        (BASE, True),
        (DOCSTRING_REWORD, True),
        (COMMENT_ONLY, True),
        (CODE_CHANGE, False),
        (MIXED, False),
        (STRING_VALUE, False),
        (BROKEN_SYNTAX, False),
    ],
)
def test_semantics_match_reads_past_prose_alone(after: str, *, expected: bool) -> None:
    assert semantics_match(BASE, after) is expected


def _git(repo: Path, *args: str) -> None:
    subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=repo,
        capture_output=True,
        encoding="utf-8",
        check=True,
    )


def _repo_with_edit(root: Path, after: str) -> Path:
    """Build a repository whose branch tip carries ``after`` on the module."""
    repo = root / "repo"
    (repo / MODULE_PATH.parent).mkdir(parents=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "gate@example.invalid")
    _git(repo, "config", "user.name", "Gate")
    (repo / MODULE_PATH).write_text(BASE, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "--no-gpg-sign", "-m", "seed")
    _git(repo, "checkout", "-b", "branch")
    (repo / MODULE_PATH).write_text(after, encoding="utf-8")
    _git(repo, "commit", "--no-gpg-sign", "-am", "edit")
    return repo


@pytest.mark.parametrize(
    ("after", "expected"),
    [
        (DOCSTRING_REWORD, set()),
        (CODE_CHANGE, {"proofhouse_python_lib.errors"}),
    ],
)
def test_changed_modules_skips_a_prose_only_edit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    after: str,
    expected: set[str],
) -> None:
    monkeypatch.chdir(_repo_with_edit(tmp_path, after))
    assert _changed_modules("main") == expected
