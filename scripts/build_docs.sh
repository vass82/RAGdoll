#!/usr/bin/env bash
# Generate the coverage reports, then build the Sphinx documentation.
# The HTML build fails if htmlcov/ is missing, so run this script from any directory.
set -euo pipefail

cd "$(dirname "$0")/.."

uv run --locked pytest \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=xml \
    --cov-report=html

uv run --locked --group docs sphinx-build \
    --fail-on-warning \
    --keep-going \
    --builder html \
    docs/source docs/_build/html
