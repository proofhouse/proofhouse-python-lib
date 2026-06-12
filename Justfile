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

# Build the sdist and wheel
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist .pytest_cache

# --- Test ---

# Run tests
test *args:
    uv run pytest "$@"
