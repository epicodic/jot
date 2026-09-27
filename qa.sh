#!/usr/bin/env bash
# Local QA: formats in place, then runs the same checks as CI.
set -euo pipefail

uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
