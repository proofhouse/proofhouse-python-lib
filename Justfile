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

# Build metadata. `source_date_epoch` is the committer date as a unix
# timestamp, not build invocation time, so two builds of the same
# commit see the same instant wherever SOURCE_DATE_EPOCH is honored.

source_date_epoch := `git log -1 --format=%ct 2>/dev/null || echo "0"`

# Default recipe
default: test

# --- Setup ---

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
    rm -rf dist .pytest_cache

# --- Format ---

# Format Markdown files (whitespace, list markers, code fence styles).
# Rewrites in place. Pair with `fix-markdown` for semantic lint fixes.
format-markdown *args:
    rumdl fmt {{ if args == "" { "." } else { args } }}

# --- Fix ---

# Apply rumdl's auto-fixable rules to Markdown files. Complement to
# `format-markdown` (which only rewrites whitespace and ordering, not
# semantic lints).
fix-markdown *args:
    rumdl check --fix {{ if args == "" { "." } else { args } }}

# --- Lint ---

# Lint prose in Markdown files and source comments via vale. Glob
# excludes the LICENSE (canonical Apache 2.0 text), the auto-generated
# changelog, vale's own style packages, scratch dirs, the gitignored
# agent worktrees under .claude/worktrees/ (whose nested virtualenvs
# vale would otherwise crawl), the COMMIT_AGENTMSG draft (the
# `lint-commit-msg` recipe owns that one under the stricter commit
# scope), the virtualenv, build output, and the pytest cache (pytest
# drops a README.md in there); the per-file-type rules in .vale.ini
# decide what else gets inspected.
lint-prose *args:
    vale --glob='!{LICENSE,CHANGELOG.md,.vale/*,tmp/*,.claude/worktrees/*,COMMIT_AGENTMSG,.venv/*,dist/*,.pytest_cache/*}' {{ if args == "" { "." } else { args } }}

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

# --- Test ---

# Run tests
test *args:
    uv run pytest "$@"

# --- Dependencies ---

# Check that uv.lock is in sync with pyproject.toml. CI runs this on
# every PR; contributors run `uv lock` and commit the result.
lock-check:
    uv lock --check
