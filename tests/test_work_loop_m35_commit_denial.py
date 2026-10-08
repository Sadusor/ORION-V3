"""M3.5 evidence must never be promoted from fixture PASS to proposal PASS."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pytest

from orion_v3.work_loop.m35_experimental_cycle import run_experimental_cycle


class FakeCompleted:
    returncode = 0
    stderr = ""
    stdout = "\n".join((
        "M35_FIXED_ACTION> PASS_APPCONTAINER_EXECUTED",
        "INSIDE_WRITE> ALLOW",
        "OUTSIDE_READ> DENY",
        "OUTSIDE_WRITE> DENY",
        "OUTSIDE_UNCHANGED> True",
        "PROFILE_DELETE_HRESULT> 0x00000000",
    ))


def test_stop_after_native_evidence_blocks_vault_commit():
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(Path.cwd())) as temp:
        calls = iter((False, True))
        with patch("orion_v3.work_loop.m35_experimental_cycle.subprocess.run",
                   return_value=FakeCompleted()):
            with pytest.raises(RuntimeError, match="STOP before Vault record"):
                run_experimental_cycle(Path(temp).parent, Path(__file__).resolve(),
                                       "test-revision", stop_requested=lambda: next(calls))


def test_native_failure_blocks_vault_commit():
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(Path.cwd())) as temp:
        class Failed:
            returncode = 1
            stdout = ""
            stderr = "native failed"
        with patch("orion_v3.work_loop.m35_experimental_cycle.subprocess.run",
                   return_value=Failed()):
            with pytest.raises(RuntimeError, match="native fixture evidence failed"):
                run_experimental_cycle(Path(temp).parent, Path(__file__).resolve(),
                                       "test-revision", stop_requested=lambda: False)
