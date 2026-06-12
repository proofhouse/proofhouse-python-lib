# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Tests for the package version metadata."""

import importlib
import importlib.metadata

import pytest

import proofhouse_python_lib


def test_version_matches_installed_metadata() -> None:
    expected = importlib.metadata.version("proofhouse-python-lib")
    assert proofhouse_python_lib.__version__ == expected


def test_version_falls_back_to_dev_when_metadata_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    try:
        assert importlib.reload(proofhouse_python_lib).__version__ == "dev"
    finally:
        monkeypatch.undo()
        importlib.reload(proofhouse_python_lib)
