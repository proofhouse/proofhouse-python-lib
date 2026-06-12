# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Reference library for the Proofhouse Python lib reference repository."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("proofhouse-python-lib")
except PackageNotFoundError:
    __version__ = "dev"
