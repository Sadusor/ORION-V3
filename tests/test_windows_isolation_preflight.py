"""Pure fail-closed tests: no process or OS sandbox launched."""
import pytest
from orion_v3.work_loop.windows_isolation_preflight import inspect_workspace

class Stop:
    def __init__(self, requested=False, fail=False):
        self.requested, self.fail = requested, fail
    def stop_requested(self):
        if self.fail:
            raise OSError("disconnected")
        return self.requested

@pytest.mark.parametrize("stop,platform,workspace", [
    (None, "win32", "E:\\probe"),
    (Stop(True), "win32", "E:\\probe"),
    (Stop(fail=True), "win32", "E:\\probe"),
    (Stop(), "linux", "E:\\probe"),
    (Stop(), "win32", "relative"),
    (Stop(), "win32", "C:\\probe"),
    (Stop(), "win32", "E:\\probe"),
])
def test_preflight_always_blocks(stop, platform, workspace):
    result = inspect_workspace(workspace, stop, platform=platform)
    assert not result.ready
    assert result.reason
