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

# --- Test ---

# Run tests
test *args:
    uv run pytest "$@"
