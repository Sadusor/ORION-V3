"""Additional STOP coordinator regression matrix; no real execution."""
import pytest
from orion_v3.work_loop.commit_coordinator import CommitCoordinator, CommitStopped

class Source:
    def __init__(self, mode):
        self.mode = mode
        self.calls = 0
    def stop_requested(self):
        self.calls += 1
        if self.mode == "error":
            raise OSError("STOP unavailable")
        return self.mode == "active"

@pytest.mark.parametrize("mode", ["active", "error", "local_stop", "stale", "local_then_active", "resume_then_active"])
def test_stop_matrix_rejects(mode):
    source = Source("clear")
    gate = CommitCoordinator(stop_source=source)
    old = gate.snapshot()
    if mode in ("active", "error"):
        source.mode = mode
    elif mode == "local_stop":
        gate.stop()
    elif mode == "stale":
        gate.stop()
        gate.resume()
    elif mode == "local_then_active":
        gate.stop()
        source.mode = "active"
    else:
        gate.stop()
        gate.resume()
        source.mode = "active"
    with pytest.raises(CommitStopped):
        with gate.commit_window(old):
            raise AssertionError("must not enter")
    assert source.calls >= 1

@pytest.mark.parametrize("cycles", [0, 1, 2, 3])
def test_resume_generation_is_monotonic(cycles):
    gate = CommitCoordinator()
    initial = gate.snapshot()
    for _ in range(cycles):
        gate.stop()
        gate.resume()
    assert gate.snapshot() == initial + 2 * cycles
    with gate.commit_window(gate.snapshot()):
        pass
