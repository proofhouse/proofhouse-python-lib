set unstable := true
set positional-arguments := true

# Run [script] recipes under bash rather than the default sh. On Linux
# sh is dash, which lacks [[ ]], <<<, and set -o pipefail — constructs
# [script] recipes rely on. Under dash such recipes either hard-fail
# (on set -o pipefail) or silently no-op (a [[ test that errors inside
# an if never trips set -e, so the failure branch is skipped). macOS
# sh is bash, which is why that breakage stays hidden until CI runs
# on Linux.
set script-interpreter := ['bash', '-eu']

# Locate a Docker-compatible container runtime. Probe PATH first, then
# well-known install locations so the recipe still works inside agentic
# harnesses or sandboxes that strip /usr/local/bin from PATH. Override by
# setting CONTAINER_RUNTIME in the environment.
container_runtime := env("CONTAINER_RUNTIME", `bash -c '
    docker_path=$(command -v docker 2>/dev/null || true)
    podman_path=$(command -v podman 2>/dev/null || true)
    for p in "$docker_path" \
             /usr/local/bin/docker \
             /opt/homebrew/bin/docker \
             /Applications/Docker.app/Contents/Resources/bin/docker \
             "$HOME/.orbstack/bin/docker" \
             "$HOME/.rd/bin/docker" \
             "$podman_path" \
             /opt/podman/bin/podman; do
        if [ -n "$p" ] && [ -x "$p" ]; then echo "$p"; exit 0; fi
    done
    echo docker
'`)

# actionlint version pin. The upstream image bundles actionlint (and the
# shellcheck it shells out to) at a known version, so we pin the image
# by digest rather than install either tool on the host. Renovate
# tracks the version + digest pair via the Justfile customManager in
# the shared org preset (see .github/renovate.json5).
#
# renovate: datasource=docker depName=rhysd/actionlint
actionlint_version := "1.7.12"
actionlint_image := "docker.io/rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667"

# actionlint invocation. Mounts the repo read-only at /repo with -w /repo
# so actionlint finds .github/workflows/ and .github/actionlint.yaml.
# DOCKER_CONFIG points at a fresh empty directory so docker skips the
# osxkeychain credential helper (public Docker Hub pulls don't need it,
# and sandboxed environments can't always reach the helper binary);
# PATH gets the runtime's directory prepended for cases where docker
# itself isn't on the calling shell's PATH.
actionlint := 'DOCKER_CONFIG="$(mktemp -d)" PATH="$(dirname ' + container_runtime + '):$PATH" ' + container_runtime + ' run --rm -v "$(pwd):/repo:ro" -w /repo ' + actionlint_image

# Build metadata. `source_date_epoch` is the committer date as a unix
# timestamp, not build invocation time, so two builds of the same
# commit see the same instant wherever SOURCE_DATE_EPOCH is honored.

source_date_epoch := `git log -1 --format=%ct 2>/dev/null || echo "0"`

# Default recipe
default: test

# --- Setup ---

# Set up development environment. New contributors run this once after
# cloning. Idempotent: re-running upgrades dependencies and refreshes
# Vale's synced style packages.
setup:
    just install-brew
    just install-tools

# Install Homebrew dependencies from Brewfile.
install-brew:
    brew bundle check || brew bundle install

# Refresh non-brew tooling. Today that means Vale's synced style
# packages; grows as new sync-style tools land.
install-tools:
    vale sync

# Sync Vale styles and dictionaries. Run once after cloning the repo,
# and whenever .vale.ini's Packages list changes. CI runs this before
# `just lint-prose`.
vale-sync:
    vale sync

# --- Build ---

# uv_build stamps fixed timestamps into its archives (1980-01-01 in
# the wheel, the unix epoch in the sdist) rather than reading
# SOURCE_DATE_EPOCH, so builds of the same tree match bit for bit by
# construction. Exporting the epoch anyway pins any tool in the build
# path that does honor it, at no cost when none does.

# Build the sdist and wheel
build:
    SOURCE_DATE_EPOCH={{ source_date_epoch }} uv build

# Build twice into separate temp dirs and fail if the wheel or sdist
# digests differ between runs. Empirical backstop for the
# reproducibility contract above; runs without touching dist/.
[script]
build-repro-check:
    out_a=$(mktemp -d)
    out_b=$(mktemp -d)
    trap 'rm -rf "$out_a" "$out_b"' EXIT
    SOURCE_DATE_EPOCH={{ source_date_epoch }} uv build --out-dir "$out_a"
    SOURCE_DATE_EPOCH={{ source_date_epoch }} uv build --out-dir "$out_b"
    digests=$(cd "$out_a" && shasum -a 256 -- *.whl *.tar.gz)
    if ! (cd "$out_b" && shasum -a 256 --check --strict <<< "$digests"); then
        echo "artifact digests differ between runs — build is not reproducible" >&2
        exit 1
    fi

# Clean build artifacts
clean:
    rm -rf dist .pytest_cache .hypothesis htmlcov coverage.xml
    rm -f .coverage .coverage.*

# --- Format ---

# Format Python source in place via ruff's formatter. The read-only
# counterpart `lint-ruff-format` runs in CI and the aggregator.
format *args:
    uv run ruff format {{ args }}

# Format Markdown files (whitespace, list markers, code fence styles).
# Rewrites in place. Pair with `fix-markdown` for semantic lint fixes.
format-markdown *args:
    rumdl fmt {{ if args == "" { "." } else { args } }}

# Format JSON / JS / TS files in place via biome's formatter.
format-config *args:
    biome format --write {{ if args == "" { "." } else { args } }}

# --- Fix ---

# Apply ruff's auto-fixes, then format. The order matters: `check
# --fix` can leave code the formatter wants to reflow (dropped
# arguments, collapsed branches), so the format pass runs last.
fix *args:
    uv run ruff check --fix {{ args }}
    uv run ruff format {{ args }}

# Apply rumdl's auto-fixable rules to Markdown files. Complement to
# `format-markdown` (which only rewrites whitespace and ordering, not
# semantic lints).
fix-markdown *args:
    rumdl check --fix {{ if args == "" { "." } else { args } }}

# --- Lint ---

# Aggregator over the Python source gates plus actionlint. CI's lint
# job invokes only this recipe, so wiring up a new gate means appending
# one dependency here instead of editing workflow YAML.
lint-py-all: lint-ruff-format lint-ruff lint-types lint-complexity lint-deadcode lint-dup-code lint-imports lint-bandit lint-reuse lint-workflows

# Run every linter that operates on the source tree. Aggregator over
# the Python gates (via `lint-py-all`), prose (vale), spelling
# (cspell), Markdown (rumdl), config / JS / TS (biome), and YAML
# (yamllint).
lint: lint-py-all lint-prose lint-spelling lint-markdown lint-config lint-yaml

# Check that ruff's formatter would change nothing. Read-only twin of
# `just format`. The path-less invocation deliberately walks the whole
# tree, tests included — `[tool.ruff] src` names import-resolution
# roots, not scan scope.
lint-ruff-format *args:
    uv run ruff format --check {{ args }}

# Lint Python source against the ruff ruleset configured in
# pyproject.toml ([tool.ruff.lint] selects ALL with documented
# exemptions). The path-less invocation deliberately walks the whole
# tree, tests included — `[tool.ruff] src` names import-resolution
# roots, not scan scope.
lint-ruff *args:
    uv run ruff check {{ args }}

# Type-check src and tests with pyrefly. [tool.pyrefly] in
# pyproject.toml starts from the strict preset and pins every
# diagnostic kind to error severity, so this gate fails on any
# finding pyrefly can produce, untyped defs included.
lint-types *args:
    uv run pyrefly check {{ args }}

# Score every function's cognitive complexity with complexipy; any
# score above the ceiling fails the run. Scope and ceiling come from
# [tool.complexipy] in pyproject.toml.
lint-complexity:
    uv run complexipy

# Report unused definitions with vulture, which pairs every name
# defined under the [tool.vulture] paths in pyproject.toml against
# the names used there. With src and tests in one scan, the tests
# stand in for downstream callers of the published API, so this gate
# asks "does anything exercise this?" of every public name.
lint-deadcode:
    uv run vulture

# Find copy-pasted logic with pylint's similarities checker, the only
# message the [tool.pylint] tables in pyproject.toml leave enabled.
# pylint accepts the directories to scan solely as command-line
# arguments, which makes this recipe the home of the src and tests
# scope.
lint-dup-code:
    uv run pylint src tests

# Check the tree against the REUSE specification: every tracked file
# must name Apache-2.0 and its copyright holder, either inline (.py
# sources keep their two-line SPDX headers) or through the bulk
# annotations in REUSE.toml (configs, the lockfile, formats with no
# comment syntax). Serial on purpose: at a few dozen files the
# default worker pool only adds startup cost, and the serial path
# also works in locked-down dev sandboxes that refuse the pool's
# named semaphores.
lint-reuse:
    uv run reuse --no-multiprocessing lint

# Verify the package's import graph against the [tool.importlinter]
# contracts in pyproject.toml: the expression pipeline stages stay
# layered, and none of them imports the shipped testing helpers. The
# bare command is import-linter's own CLI, not this recipe recursing.
lint-imports:
    uv run lint-imports

# Run bandit's static security analysis over the shipped source. ruff
# already carries the S (flake8-bandit) rules under its `select = ["ALL"]`
# set, but the two are not the same scanner: ruff reimplements a subset of
# bandit's checks against its own syntax tree, while bandit keeps the full
# upstream catalog — B-prefixed test IDs ruff has never ported — and
# tracks new advisory patterns on its own release cadence. Running both
# pairs the fast in-editor S diagnostics with the deeper second read that
# notices what the port skipped. `-c pyproject.toml` loads the
# [tool.bandit] table; `-r src` walks the package recursively. This is the
# analog of the Go twin enabling gosec inside golangci-lint, so it rides
# the same lint gate rather than a standalone job — fast enough to block a
# merge from the lint set, where its non-zero exit on any finding stops
# the branch.
lint-bandit:
    uv run bandit -c pyproject.toml -r src

# Lint prose in Markdown files and source comments via vale. Glob
# excludes the LICENSE (canonical Apache 2.0 text), the auto-generated
# changelog, vale's own style packages, scratch dirs, the gitignored
# agent worktrees under .claude/worktrees/ (whose nested virtualenvs
# vale would otherwise crawl), the COMMIT_AGENTMSG draft (the
# `lint-commit-msg` recipe owns that one under the stricter commit
# scope), the virtualenv, build output, and the pytest and complexipy
# caches (both drop a README.md in there); the per-file-type rules in
# .vale.ini decide what else gets inspected.
lint-prose *args:
    vale --output=proofhouse-agent.tmpl --glob='!{LICENSE,CHANGELOG.md,.vale/*,tmp/*,.claude/worktrees/*,COMMIT_AGENTMSG,.venv/*,dist/*,.pytest_cache/*,.complexipy_cache/*}' {{ if args == "" { "." } else { args } }}

# Check spelling across the tree against the project dictionary at
# .cspell-words.txt. cspell ignores binaries, generated files, the
# virtualenv, and build output via the ignorePaths block in
# .cspell.jsonc. The COMMIT_AGENTMSG draft gets excluded here and
# checked by `lint-commit-msg` instead, so a work-in-progress message
# never trips the tree-wide spell check.
lint-spelling *args:
    cspell --config .cspell.jsonc --no-summary --no-progress --no-must-find-files --exclude COMMIT_AGENTMSG {{ if args == "" { "." } else { args } }}

# Lint Markdown files against the project's .rumdl.toml ruleset.
# rumdl handles structural lints (heading style, list marker style,
# code fence style); vale handles prose.
lint-markdown *args:
    rumdl check {{ if args == "" { "." } else { args } }}

# Lint JSON / JS / TS files via biome. Recommended ruleset, biome's
# own formatter; covers config files (biome.json, .cspell.jsonc) and
# any future scripts under .github/actions/.
lint-config *args:
    biome check --files-ignore-unknown=true {{ if args == "" { "." } else { args } }}

# Lint YAML files (config, workflows, action definitions). --strict
# treats warnings as errors so the gate matches CI behavior; per-rule
# tuning lives in .yamllint.yaml.
lint-yaml *args:
    yamllint --strict {{ if args == "" { "." } else { args } }}

# Lint GitHub Actions workflow files via actionlint. actionlint walks
# `.github/workflows/` by default, parses each workflow, and flags
# unknown actions, mis-typed expressions, shellcheck issues inside
# `run:` blocks, and SHA-pin drift. Complements `lint-yaml` (which
# checks YAML structure) with workflow-shape rules yamllint can't see.
# Runs from the digest-pinned Docker image declared at the top of this
# file; Renovate bumps the version + digest via the shared Justfile
# customManager.
lint-workflows:
    {{ actionlint }}

# Pre-validate a drafted commit message against the same gates the
# commit-msg hook runs, so message problems surface while iterating
# rather than at commit time. Reads the draft from the repo-root
# COMMIT_AGENTMSG file (gitignored; see AGENTS.md for the workflow) and
# runs the commit-msg stage through prek, which fires the four shared
# hooks from proofhouse/pre-commit-hooks: commit-trailers, commitlint,
# vale-commit-msg, and cspell-commit-msg. The real gate stays the prek
# commit-msg hook on .git/COMMIT_EDITMSG; this recipe only mirrors it.
# Commit the validated draft with `git commit -F COMMIT_AGENTMSG`.
lint-commit-msg:
    prek run --stage commit-msg --commit-msg-filename COMMIT_AGENTMSG

# --- Test ---

# Run tests. The property suite under tests/property loads hypothesis's
# `dev` profile by default (50 examples, a fast inner loop); set
# HYPOTHESIS_PROFILE=ci for the 500-example deadline-free search CI runs.
# A failing property replays its falsifying example from the local
# .hypothesis database on the next run, so the case sticks until fixed.
#
# pytest-randomly shuffles the collection order every run and prints the
# seed it chose; pin that seed to replay an order that exposed a leak —
# `just test -p randomly --randomly-seed=12345`. Runs stay serial here so
# the seed line and any failure read cleanly; pass `just test -n auto` to
# fan the suite across cores via xdist, which is the shape CI's coverage
# slots run under.
test *args:
    uv run pytest "$@"

# Run the suite under branch coverage and hold it to the floor. A bare
# `--cov` reads `source` from [tool.coverage.run], so the package gets
# measured rather than the tests; `--cov-branch` records which arm of
# each fork ran. The report and the fail_under threshold come from
# [tool.coverage.report]. This is the inner loop: run it, read the
# Missing column, write the test that reaches the unreached arm.
cover:
    uv run pytest --cov --cov-branch

# Build the line-by-line HTML report under htmlcov/ and print where it
# lands. Each statement and branch arm is shaded by whether a test
# reached it, which pins down the exact line a new test still owes.
cover-html:
    uv run pytest --cov --cov-branch
    uv run coverage html
    @echo "open htmlcov/index.html"

# Write Cobertura XML from whatever .coverage already holds. That format
# is what diff-cover reads and what the CI upload action publishes, so
# this assumes a `cover` or `cover-slot` run produced the data first.
cover-xml:
    uv run coverage xml -o coverage.xml

# Fail when a line touched since [base] is not covered. The whole-tree
# floor already sits at 100%, so on a clean branch this adds nothing; it
# earns its keep by catching a diff that strips coverage from edited
# lines before the slower combined total recomputes in CI. Reads
# coverage.xml, so run `cover-xml` first (CI does).
cover-diff base="origin/main":
    uv run diff-cover coverage.xml --compare-branch={{ base }} --fail-under=100

# Re-read the existing .coverage data and re-check the threshold without
# rerunning the suite — handy after editing exclude_also to confirm the
# total still holds without paying for another run.
cover-check:
    uv run coverage report

# Fold every slot's data file into one .coverage, hold the merged total
# to the floor, and render the combined Cobertura. This is the binding
# gate: a branch no single platform happens to run still has to be
# reached somewhere, and the merged report is the proof. The CI coverage
# job runs this after pulling down the per-slot artifacts.
cover-combine:
    uv run coverage combine
    uv run coverage report --fail-under=100
    uv run coverage xml -o coverage.xml

# Record one matrix slot's coverage into a slot-named data file and
# render that slot's Cobertura. COVERAGE_FILE tags the data file with
# the slot so the downstream job can combine every slot losslessly;
# --cov-fail-under=0 hands the threshold off to that combined check,
# since one slot need not carry the whole library on its own. CI passes
# the os/python pair as the slot name. `-n auto` spreads the run across
# the slot's cores: pytest-cov sums each worker's tally back into the one
# COVERAGE_FILE, so the slot's number stays whole under the split.
[script]
cover-slot slot="local":
    export COVERAGE_FILE=".coverage.{{ slot }}"
    uv run pytest --cov --cov-branch --cov-fail-under=0 -n auto
    uv run coverage xml -o coverage.xml

# --- Mutation ---

# Wall-clock seconds cosmic-ray allows one mutated suite run before it
# files the mutant incompetent instead of survived. cosmic-ray.toml
# carries the same default; both recipes here splice this value over it,
# so a contributor on a slow machine or a busier-than-usual runner widens
# the ceiling once through MUTATION_TIMEOUT rather than editing the config.
# Unlike the Go side's coefficient that scales a measured baseline, this
# is the raw budget cosmic-ray expects.
mutation_timeout := env("MUTATION_TIMEOUT", "30.0")

# Mutate a single module for a tight edit-rerun loop. Point it at the file
# you just touched — the precedence table in parser.py, the Fraction
# arithmetic in evaluator.py, the bracketing rules in formatter.py — and
# cosmic-ray rewrites one construct at a time, replays the suite, and
# files each mutant KILLED, SURVIVED, or incompetent. The SURVIVED lines
# are where the code branches but no assertion reads the difference. It
# clones cosmic-ray.toml into a scratch config with the path and budget
# overridden, runs the pragma filter so the equivalent mutants flagged in
# the source drop out before they cost a run, then prints the surviving
# set and the rate. The whole-package form below feeds the nightly.
[script]
mutate path="src/proofhouse_python_lib":
    mkdir -p .cosmic-ray
    cfg=.cosmic-ray/scoped.toml
    session=.cosmic-ray/scoped.sqlite
    sed -e 's|^module-path = .*|module-path = "{{ path }}"|' \
        -e 's|^timeout = .*|timeout = {{ mutation_timeout }}|' \
        cosmic-ray.toml > "$cfg"
    rm -f "$session"
    uv run cosmic-ray init "$cfg" "$session"
    uv run cr-filter-pragma "$session" >/dev/null
    uv run cosmic-ray exec "$cfg" "$session"
    uv run cr-report --surviving-only "$session"
    uv run cr-rate "$session"

# Sweep every shipped module. The scheduled workflow calls this and so can
# anyone vetting a release-bound change, which is why it lives in one
# recipe rather than being inlined into the YAML — the fuzz pair keeps the
# same split. module-path and the equivalent-mutant exclusions ride along
# from cosmic-ray.toml; only the budget gets overridden. The pragma filter
# retires the type-alias mutants the source marks before exec spends time
# on them. This recipe sets no passing bar: it lists what lived and exits
# zero whatever the rate, leaving the score that can block a merge to the
# diff-scoped check. Read the surviving block to find the next assertion
# worth writing.
[script]
mutate-all:
    mkdir -p .cosmic-ray
    cfg=.cosmic-ray/all.toml
    session=.cosmic-ray/all.sqlite
    sed -e 's|^timeout = .*|timeout = {{ mutation_timeout }}|' \
        cosmic-ray.toml > "$cfg"
    rm -f "$session"
    uv run cosmic-ray init "$cfg" "$session"
    uv run cr-filter-pragma "$session" >/dev/null
    uv run cosmic-ray exec "$cfg" "$session"
    uv run cr-report --surviving-only "$session"
    uv run cr-rate "$session"

# --- Security ---

# Walk the working tree and every commit in history for secrets that
# slipped into the source. `gitleaks git` diffs each commit against the
# binary's bundled regex and entropy rules; a hit reports the file,
# line, commit, and rule, enough to trace the leak without a second
# pass. A credential baked into a published wheel ships to every
# installer and lingers in the sdist's packed history, so the full
# scan guards what a release would otherwise hand out. The pin lives in
# the Brewfile and moves forward with `brew upgrade gitleaks`. This one
# stays a local recipe on purpose: GitHub's own secret scanning with
# push protection holds the same line on the hosted side, so no CI job
# duplicates it.
gitleaks:
    gitleaks git --verbose .

# Audit the resolved dependency closure against the OSV and PyPI
# advisory feeds. The subject is the lock, not the live `.venv`: pip-audit
# learns the closure from a PEP 751 pylock.toml that `uv export --frozen`
# renders straight from the committed uv.lock, so the scan covers exactly
# the transitive set a `uv sync` would install — every pinned version,
# not just the handful named in pyproject. Auditing the interpreter's
# current site-packages instead would let a stale or hand-patched
# environment drift away from what ships. The export lands in a scratch
# directory that the trap clears on exit; `--locked` tells pip-audit to
# read the pylock there rather than re-resolve. A reachable advisory
# exits non-zero, which is why this rides in the CI gate set and not only
# the Security tab. pip-audit's HTTP cache for the advisory feeds lands in
# the same scratch directory, so the run leaves nothing behind and never
# reaches for a per-user cache path a sandboxed shell may be barred from
# creating.
[script]
audit:
    work=$(mktemp -d)
    trap 'rm -rf "$work"' EXIT
    uv export --frozen --format pylock.toml -o "$work/pylock.toml" --quiet
    uv run pip-audit "$work" --locked --cache-dir "$work/cache"

# One entry point for the scanners that vet what the package hands its
# importers: gitleaks reads the history for leaked secrets, audit weighs
# the locked closure against the advisory feeds, and lint-bandit reads the
# source for insecure constructs — three angles on the same shipped
# artifact. lint-bandit also belongs to lint-py-all, so CI runs it from
# the lint gate; here it rounds out the bundle a contributor reaches for
# before a push, without retyping each scanner.
security: gitleaks audit lint-bandit

# --- Dependencies ---

# Check that uv.lock is in sync with pyproject.toml. CI runs this on
# every PR; contributors run `uv lock` and commit the result.
lock-check:
    uv lock --check

# --- Utilities ---

# Run pre-commit hooks on changed files (the everyday invocation).
prek:
    prek

# Run pre-commit hooks on every file in the tree. Useful after a
# hook config change or before a release sweep.
prek-all:
    prek run --all-files

# Install the project's pre-commit hooks (commit-msg, pre-commit,
# pre-push). New contributors run this once after `just setup`; the
# `just setup` recipe does NOT run it automatically because installing
# hooks modifies .git/ and contributors may prefer to opt in.
prek-install:
    prek install -t commit-msg -t pre-commit -t pre-push

# Generate the full CHANGELOG.md from Conventional Commit history.
# `cog changelog` emits Markdown without an H1; the pipeline prepends
# one and runs rumdl with MD024 (duplicate headings) disabled so
# adjacent releases with the same section names don't fight the
# linter.
generate-changelog:
    cog changelog | { echo "# Changelog"; cat; } | rumdl check -d MD024 --fix --stdin > CHANGELOG.md

# Preview the changelog entries since the last tagged release. Useful
# during release prep to see what `cog changelog` will emit before
# committing the regeneration.
preview-changelog:
    cog changelog --at $(git describe --tags)..HEAD -t full_hash | rumdl check -d MD041 --fix --stdin

# Generate release notes for a specific version (or for HEAD if no
# version is given). Output goes to stdout; pipe to a file or paste
# into the GitHub release body.
[script]
generate-release-notes version="":
    v=$([[ -n "{{ version }}" ]] && echo "v{{ version }}" || echo "..$(git rev-parse HEAD)")
    cog changelog --at $v -t full_hash | rumdl check -d MD024,MD041 --isolated --fix --stdin
