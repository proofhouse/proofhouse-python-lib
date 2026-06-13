# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Hypothesis profile registration for the property suite.

This conftest sits beside the property tests rather than at the suite
root because hypothesis is theirs alone: a plain `just test` of the unit
tree never collects it and so never imports hypothesis. The profiles it
registers still take effect process-wide once collected, which is all
the property runs need.

`dev` keeps local runs quick; `ci` widens the search and drops the
per-example deadline so a slow machine never times a valid case out.
`HYPOTHESIS_PROFILE=ci` in the CI environment selects the wider profile;
absent that variable the default `dev` profile loads.
"""

import os

from hypothesis import settings

settings.register_profile("dev", max_examples=50)
settings.register_profile("ci", max_examples=500, deadline=None)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
