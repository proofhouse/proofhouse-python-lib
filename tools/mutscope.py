# SPDX-License-Identifier: Apache-2.0
# Copyright Authors of Proofhouse

"""Narrow a cosmic-ray run to the modules a diff could have altered.

A whole-tree mutation pass is the nightly's job. On a pull request the gate
only cares about the slice a branch can affect: the touched first-party
modules and everyone who imports them, near or far. The reason for the second
group is behavioral. When the formatter's bracketing keys off the precedence
table and a mutant flips a comparison there, the formatter's own tests can
keep passing over a rule that no longer holds, so its module has to ride into
the scope alongside the one that changed.

The work splits into mapping and graph-walking. Changed paths under ``src``
become module names; grimp's import graph turns each into itself plus its
downstream importers; the union maps back to source paths and lands as the
``module-path`` of a config cloned from ``cosmic-ray.toml``. A diff that
leaves first-party source alone resolves to nothing, and the gate reads that
empty config as a pass with no mutants to run.

A changed file earns a place in that mapping only where the edit reaches
executable code. Both revisions parse into syntax trees, every docstring
blanks out, and the two dumps compare; an equal pair says the diff moved
nothing a mutant could rewrite, so the module stays out of the scope.
Comments never enter a tree to begin with, and a string the code reads as a
value outlives the blanking, so a reworded docstring drops away while an
edited message string, or a docstring beside a real edit, keeps its module.
Whatever the comparison cannot settle — a path the base ref never carried, a
revision that refuses to parse — keeps the module too, since the cost of a
needless mutation run is minutes and the cost of a dropped one is a hole in
the gate.

The ``--count-survivors`` mode is the other half: it consumes a
``cosmic-ray dump`` on stdin and reports the surviving tally the recipe exits
on. Keeping the JSON walk in this file rather than an inline shell line holds
it to the same type and lint bars as the scoping code.
"""

import ast
import json
import subprocess
import sys
from pathlib import Path

PACKAGE = "proofhouse_python_lib"
SRC_ROOT = Path("src")
PACKAGE_ROOT = SRC_ROOT / PACKAGE
BASE_CONFIG = Path("cosmic-ray.toml")

# The node kinds Python reads a leading string literal on as a docstring.
# Every other string, wherever it sits, is a value the code can act on.
DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _changed_files(base: str) -> list[Path]:
    """Return paths git reports differ between ``base`` and the working tip.

    The triple-dot range diffs against the merge base, so anything the base
    branch gained after the fork point stays out of this branch's tally.
    """
    out = subprocess.run(  # noqa: S603
        ["git", "diff", "--name-only", f"{base}...HEAD"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [Path(line) for line in out.splitlines() if line]


def _merge_base(base: str) -> str:
    """Return the commit where ``base`` and the working tip last agreed.

    The scoping diff runs from that fork point, so the before-image of a
    changed file has to come from there rather than from the base branch tip.
    """
    return subprocess.run(  # noqa: S603
        ["git", "merge-base", base, "HEAD"],  # noqa: S607
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()


def _blob(ref: str, path: Path) -> str | None:
    """Return the text of ``path`` at ``ref``, or None where the ref lacks it.

    A rename, an addition, or a deletion leaves one side of the pair with no
    file, and the absence reports itself rather than raising, so the caller
    can read it as the unsettled case such a pair makes.
    """
    shown = subprocess.run(  # noqa: S603
        ["git", "show", f"{ref}:{path.as_posix()}"],  # noqa: S607
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    return shown.stdout if shown.returncode == 0 else None


def _blank_docstrings(tree: ast.Module) -> None:
    """Empty every docstring in ``tree``, in place.

    The docstring is the leading string statement of a module, a class, or a
    function, and only there. Emptying the literal instead of dropping the
    statement holds each body at its original length, so a body that carries
    nothing but prose stays distinct from an empty one.
    """
    for node in ast.walk(tree):
        if not isinstance(node, DOCSTRING_OWNERS) or not node.body:
            continue
        leading = node.body[0]
        if (
            isinstance(leading, ast.Expr)
            and isinstance(leading.value, ast.Constant)
            and isinstance(leading.value.value, str)
        ):
            leading.value.value = ""


def semantics_match(before: str, after: str) -> bool:
    """Report whether two revisions of a module say the same thing to Python.

    The comparison runs over docstring-blanked syntax trees dumped without
    positions, which is what makes it read prose rather than text: comments
    and blank lines never reach a tree, and a moved line carries no position
    into the dump. A source that fails to parse answers False, the side that
    keeps the module in scope.
    """
    try:
        before_tree = ast.parse(before)
        after_tree = ast.parse(after)
    except SyntaxError:
        return False
    _blank_docstrings(before_tree)
    _blank_docstrings(after_tree)
    return ast.dump(before_tree) == ast.dump(after_tree)


def _prose_only(path: Path, merge_base: str) -> bool:
    """Report whether the diff on ``path`` leaves its executable content alone.

    Both sides come out of git rather than the working tree, which keeps the
    reading on the same range the scoping diff walks.
    """
    before = _blob(merge_base, path)
    after = _blob("HEAD", path)
    if before is None or after is None:
        return False
    return semantics_match(before, after)


def _module_name(path: Path) -> str | None:
    """Resolve a repository path to its module name, or None for a non-module.

    A path qualifies only when it ends in ``.py`` and sits inside the package
    tree. An ``__init__`` stands for its directory, so its name drops the
    final component.
    """
    if path.suffix != ".py" or PACKAGE_ROOT not in path.parents:
        return None
    relative = path.relative_to(SRC_ROOT)
    parts = relative.with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _module_path(module: str) -> Path:
    """Resolve a module name back to the source path that defines it.

    A package name with no file of its own points at its ``__init__``; a leaf
    module points at the matching ``.py``.
    """
    base = SRC_ROOT.joinpath(*module.split("."))
    return base / "__init__.py" if base.is_dir() else base.with_suffix(".py")


def _changed_modules(base: str) -> set[str]:
    """Name the first-party modules whose executable content the diff moved.

    Resolving the fork point costs a git call, so a diff that names no module
    at all skips it and the per-file reading behind it.
    """
    candidates = [
        (path, name)
        for path in _changed_files(base)
        if (name := _module_name(path)) is not None
    ]
    if not candidates:
        return set()
    merge_base = _merge_base(base)
    return {name for path, name in candidates if not _prose_only(path, merge_base)}


def compute_scope(base: str) -> set[str]:
    """Gather the changed first-party modules and everything downstream of them.

    A freshly added file nothing imports yet still enters on its own; only the
    downstream expansion needs the module to already be a node in the graph.
    """
    changed = _changed_modules(base)
    if not changed:
        return set()
    # grimp and cosmic-ray belong to the dev group, which the test matrix
    # never syncs. Importing each at its point of use, rather than at module
    # scope, lets the unit suite exercise the scoping rules on a test-group
    # environment alone.
    import grimp  # noqa: PLC0415

    graph = grimp.build_graph(PACKAGE)
    scope: set[str] = set()
    for module in changed:
        scope.add(module)
        if module in graph.modules:
            scope.update(graph.find_downstream_modules(module))
    return scope


def write_config(scope: set[str], destination: Path) -> None:
    """Render a scoped config out of the canonical one for ``scope``.

    Round-tripping through cosmic-ray's config loader carries the accepted
    equivalents, the test command, and the distributor across untouched; the
    one field this rewrites is ``module-path``, set to the scoped files.
    """
    # Deferred for the same reason grimp is, one gate up in this file.
    from cosmic_ray.config import load_config, serialize_config  # noqa: PLC0415

    config = load_config(str(BASE_CONFIG))
    config["module-path"] = sorted(str(_module_path(m)) for m in scope)
    destination.write_text(serialize_config(config), encoding="utf-8")


def count_survivors(dump: str) -> int:
    """Tally the surviving mutants across a ``cosmic-ray dump`` stream.

    Every line decodes to a ``[work-item, result]`` pair. A null result means
    the job never ran, a state a finished exec leaves behind. The walk folds
    that case in as not-survived rather than raising on it.
    """
    survivors = 0
    for line in dump.splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        result = record[1] if len(record) > 1 else None
        if result is not None and result.get("test_outcome") == "survived":
            survivors += 1
    return survivors


def _emit_scope(destination: Path, base: str) -> None:
    """Compute and persist the scoped config, logging the set to stderr.

    The chosen module set prints so a run never mutates a silent, unexplained
    scope. An empty one says as much outright.
    """
    scope = compute_scope(base)
    write_config(scope, destination)
    if scope:
        listing = " ".join(sorted(scope))
        print(f"mutation scope ({len(scope)} modules): {listing}", file=sys.stderr)
    else:
        print(
            "mutation scope: empty (no executable first-party change)",
            file=sys.stderr,
        )


def main() -> None:
    """Route the two modes the diff-mutation recipe invokes.

    A leading config-path argument selects scope-writing, with a trailing
    base ref defaulting to ``origin/main``. The survivor-count flag instead
    drains a dump from stdin and prints how many mutants lived.
    """
    if sys.argv[1] == "--count-survivors":
        print(count_survivors(sys.stdin.read()))
        return
    destination = Path(sys.argv[1])
    base = sys.argv[2] if len(sys.argv) > 2 else "origin/main"
    _emit_scope(destination, base)


if __name__ == "__main__":
    main()
