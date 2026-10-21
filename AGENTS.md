# Agent Instructions for Alfalfa

These instructions apply to any AI coding agent (Copilot, Claude, etc.) working
in this repository. CI (`.github/workflows/ci.yml`) runs pre-commit, unit
tests, simulation tests, and two integration-test jobs, and a PR/branch is not
mergeable until all of them pass. **Do not tell the user code is "ready to
push" or "should pass CI" without actually having run the checks below
locally and confirmed they pass.**

## Before saying code can be pushed

Run these in order, stopping to fix and re-run whenever something fails.
Prefer the fastest check that would catch the class of bug you introduced;
escalate to slower checks before the final go-ahead.

### 1. Pre-commit (required, fast)

```bash
pip install pre-commit   # once, if not already installed
pre-commit run --show-diff-on-failure --color=always --all-files
```

This runs autopep8, autoflake, flake8, isort, and prettier (docs/JS/YAML/etc).
Prettier and autopep8/autoflake will auto-fix files in place — re-run until
clean, then review the diff. A PR failing only on formatting (as opposed to a
real logic bug) usually means this step was skipped before pushing.

### 2. Unit tests (required, fast, seconds)

```bash
poetry install
docker compose up -d mongo redis minio mc   # unit tests need these running
poetry run pytest
```

This runs everything under `tests/` **except** tests marked `integration`,
`fmu`, `docker`, `scale`, or `api` (see `addopts` in `setup.cfg`). It does not
build or run any simulation and normally finishes in well under a minute.

**Known environment gap:** `alfalfa_worker/lib/testcase.py` imports `pyfmi`
(and transitively `matplotlib` via `data_manager.py`). Neither is a poetry
dependency — they only exist inside the worker Docker image (built from
`ghcr.io/natlabrockies/alfalfa-dependencies`). Any new test that imports
`alfalfa_worker.lib.testcase` (or anything importing it) must guard the import
with `pytest.importorskip("alfalfa_worker.lib.testcase")` so it's skipped
here instead of failing collection for the entire test run. This has broken
CI before — check for it explicitly when adding tests under `tests/worker/`.

### 3. Fast integration/simulation checks (do these before the full suite)

Full integration tests spin up the whole Docker stack (web, worker, mongo,
redis, minio) and are slow to build/run. When you only need to sanity-check a
worker/API change, run the narrowest, fastest slice first instead of the full
matrix:

```bash
docker compose up -d --scale worker=2
poetry run pytest --timeout=120 -m api                       # fastest: API contract tests
poetry run pytest --timeout=600 -m integration -k "modelica or basic_operations or broken_models or schedule_override"
```

`tests/integration/test_modelica.py`, `test_basic_operations.py`,
`test_broken_models.py`, and `test_schedule_override.py` use small/fast
models (FMU or trivial OSW) and are the "fast simulations." Avoid running
`tests/integration/test_small_office_osw.py` (full OpenStudio/EnergyPlus
simulation) or `-m scale` (multi-worker load test) unless the change actually
touches OpenStudio job handling, worker scaling, or you are doing the final
pre-push validation — they are the slow paths and should be run last, only
when the fast checks pass and the change plausibly affects that path.

### 4. Full suite (only when warranted)

Run the complete matrix mirroring CI before declaring larger/riskier changes
final:

```bash
poetry run pytest --timeout=120 -m api
poetry run pytest --timeout=600 -m integration
poetry run pytest -m scale
```

If the change touches `alfalfa_worker/jobs/`, also run the docker-based job
tests the `simulation-tests` CI job runs (inside the worker container):

```bash
docker exec alfalfa-worker-1 bash -c "cd /alfalfa && poetry run pytest -m docker tests/jobs"
```

Tear down containers afterward: `docker compose down`.

## Summary checklist before saying "ready to push"

- [ ] `pre-commit run --all-files` is clean (no modified files, no failures)
- [ ] `poetry run pytest` (unit tests) passes
- [ ] Fast integration tests relevant to the change pass (`-m api`, and the
      fast subset of `-m integration`)
- [ ] Full integration/simulation suite run at least once if the change is
      non-trivial or touches simulation/job code
