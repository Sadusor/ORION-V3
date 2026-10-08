"""Negative safety gates for M3.5 fixture-only qualification."""
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from orion_v3.work_loop.m35_experimental_cycle import run_experimental_cycle


def test_stop_blocks_before_child_even_with_existing_probe():
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(Path.cwd())) as folder:
        # Existing executable is irrelevant: STOP must fire before execution.
        probe = Path(__file__).resolve()
        with pytest.raises(RuntimeError, match="STOP before fixture"):
            run_experimental_cycle(Path(folder).parent, probe, "test-revision",
                                   stop_requested=lambda: True)


def test_missing_probe_fails_closed():
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(Path.cwd())) as folder:
        with pytest.raises((ValueError, FileNotFoundError)):
            run_experimental_cycle(Path(folder).parent, Path(folder) / "missing.dll",
                                   "test-revision", stop_requested=lambda: False)


def test_unreadable_stop_fails_closed():
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(Path.cwd())) as folder:
        def unavailable():
            raise RuntimeError("STOP unavailable")
        with pytest.raises(RuntimeError, match="STOP unavailable"):
            run_experimental_cycle(Path(folder).parent, Path(__file__).resolve(),
                                   "test-revision", stop_requested=unavailable)
