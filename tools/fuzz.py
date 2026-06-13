# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Drive HypoFuzz over the property suite for a bounded budget.

`hypothesis fuzz` is a coverage-guided search that runs until interrupted. It
has no time flag of its own, and it returns on its own only once every target
has failed. Neither shape gates cleanly, so this wrapper supplies the missing
budget: it starts the search, gives it FUZZ_TIME, and then stops it.

Detection is split from the search. A failing input HypoFuzz turns up gets
saved to the shared `.hypothesis` database the moment it appears, so the
verdict comes from a plain pytest replay of the property suite afterward. That
replay reads the same database, reruns any saved counterexample, and exits
non-zero when one reproduces. The recipe surfaces that exit code, so a crasher
fails the run whether or not the search was still going when the budget ran
out.

The budget is read from FUZZ_TIME as a count of seconds or a duration suffixed
`s`, `m`, or `h`, matching the dial the Go twin's fuzz recipe takes so the two
lanes share one mental model. The inner loop runs a short default; the nightly
passes a longer one.
"""

import os
import signal
import subprocess
import time

PROPERTY_SUITE = "tests/property"
DEFAULT_BUDGET = "30s"
# Grace after the budget for HypoFuzz to flush its database and wind down
# its worker pool before a forced stop.
SHUTDOWN_GRACE_SECONDS = 20.0
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600}


def parse_budget(raw: str) -> float:
    """Read a duration or a bare seconds count into a float of seconds.

    A trailing ``s``, ``m``, or ``h`` scales the leading number; a plain number
    is already seconds. Anything else, or a non-positive result, ends the run
    rather than a silent fallback that would hide a mistyped budget.
    """
    text = raw.strip()
    unit = _UNIT_SECONDS.get(text[-1:])
    number = text[:-1] if unit is not None else text
    try:
        seconds = float(number) * (unit if unit is not None else 1)
    except ValueError:
        message = f"could not read FUZZ_TIME {raw!r}: want seconds or a duration"
        raise SystemExit(message) from None
    if seconds <= 0:
        message = f"FUZZ_TIME must be positive, got {raw!r}"
        raise SystemExit(message)
    return seconds


def run_fuzzer(budget: float) -> None:
    """Search the property suite with HypoFuzz, then stop it after ``budget``.

    The search runs as a child process so the budget can be enforced from
    here. Once it elapses the child receives SIGINT, the signal HypoFuzz reads
    as a clean stop. A grace window then lets its findings flush before a
    forced stop. An early exit (the all-targets-failed case) is left alone.
    """
    command = [
        "uv",
        "run",
        "hypothesis",
        "fuzz",
        "--no-dashboard",
        "--",
        PROPERTY_SUITE,
    ]
    proc = subprocess.Popen(command)  # noqa: S603
    deadline = time.monotonic() + budget
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(1)
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=SHUTDOWN_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def replay_suite() -> int:
    """Rerun the property suite under pytest and return its exit code.

    Pytest reads the same ``.hypothesis`` database HypoFuzz just wrote, so a
    counterexample the search saved replays here and fails. A clean search
    leaves the database with nothing new to reproduce, and this pass is green.
    """
    return subprocess.run(  # noqa: S603
        ["uv", "run", "pytest", PROPERTY_SUITE],  # noqa: S607
        check=False,
    ).returncode


def main() -> None:
    """Fuzz for the FUZZ_TIME budget, then gate on the replay's verdict."""
    budget = parse_budget(os.environ.get("FUZZ_TIME", DEFAULT_BUDGET))
    run_fuzzer(budget)
    raise SystemExit(replay_suite())


if __name__ == "__main__":
    main()
