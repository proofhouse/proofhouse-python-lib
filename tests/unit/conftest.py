# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Import path setup for the tests that read the tools directory.

The scripts under `tools/` run from the shell and carry no package
marker, so nothing puts the repository root on the import path for
them. Adding it here lets `test_mutscope.py` import the scoping helper
the way any other module imports its subject, rather than loading the
file through a hand-rolled spec.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
