"""Unit tests for TestCase input range checking.

These guard the tolerance added for plain (non-BOPTEST) FMUs, whose variables
may not declare a min/max. In that case the range clamp must be skipped rather
than crashing on a comparison against None. Normal clamping behaviour must be
preserved for FMUs that do declare bounds.

Pure logic: TestCase.__new__ is used to bypass __init__ (which would load an
FMU) so no FMU/pyfmi runtime or external services are required at runtime.
However, alfalfa_worker.lib.testcase imports pyfmi (and, transitively,
matplotlib via data_manager) at module scope. Those packages are only
installed inside the worker Docker image (they are not poetry dependencies),
so they aren't available in the unit-test/integration-test CI jobs. Skip
collection there instead of erroring; the test still runs for real wherever
the worker's full dependency set is installed (e.g. inside the worker Docker
image).
"""
import pytest

_testcase_module = pytest.importorskip("alfalfa_worker.lib.testcase")
TestCase = _testcase_module.TestCase


def _make_testcase(minimum, maximum):
    tc = TestCase.__new__(TestCase)
    tc.inputs_metadata = {"u": {"Minimum": minimum, "Maximum": maximum}}
    return tc


def test_check_value_min_max_skips_when_both_bounds_none():
    # Non-BOPTEST FMU variable with no declared min/max -> value passes through.
    tc = _make_testcase(None, None)
    assert tc._check_value_min_max("u", 1234.5) == 1234.5


def test_check_value_min_max_skips_when_one_bound_none():
    assert _make_testcase(0.0, None)._check_value_min_max("u", -5.0) == -5.0
    assert _make_testcase(None, 10.0)._check_value_min_max("u", 99.0) == 99.0


def test_check_value_min_max_clamps_when_bounds_present():
    tc = _make_testcase(0.0, 10.0)
    # within range -> unchanged
    assert tc._check_value_min_max("u", 5.0) == 5.0
    # above max -> clamped to max
    assert tc._check_value_min_max("u", 15.0) == 10.0
    # below min -> clamped to min
    assert tc._check_value_min_max("u", -3.0) == 0.0
