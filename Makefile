# Canonical Foreman Makefile contract. See docs/makefile-contract.md.
#
# Every pipeline consumer depends ONLY on these targets:
#   check  — lint + test; the tag CI quality gate
#   test   — the test suite
#   build  — install/compile the package so it is runnable (smoke-run: make build)
#   run    — a representative smoke invocation of the REAL entrypoint on a
#            bundled fixture, producing real output (smoke-run: make run)
#
# The completion smoke-run judges WORKS vs HOLLOW from what `make run` prints,
# so `run` MUST exercise the real tool on real input — not just print usage.
# Wire PACKAGE/SMOKE_ARGS (or replace the run recipe) to the real entrypoint and
# a fixture shipped under examples/ as the tool takes shape.
PACKAGE ?= deportation_foia_normalizer
SMOKE_ARGS ?= examples/sample.csv

.PHONY: lint test check build run

lint:
	ruff check .

test:
	pytest

check: lint test

build:
	pip install -e ".[dev]"

run:
	python -m $(PACKAGE) $(SMOKE_ARGS)
