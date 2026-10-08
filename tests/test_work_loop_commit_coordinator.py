"""STOP ordering tests for an in-process commit coordinator."""
from threading import Event, Thread
import pytest
from orion_v3.work_loop.commit_coordinator import CommitCoordinator, CommitStopped


def test_commit_allowed_before_stop():
    c = CommitCoordinator()
    with c.commit_window(c.snapshot()):
        assert True


def test_stop_blocks_commit():
    c = CommitCoordinator()
    generation = c.snapshot()
    c.stop()
    with pytest.raises(CommitStopped):
        with c.commit_window(generation):
            pass


def test_resume_does_not_revalidate_stale_generation():
    c = CommitCoordinator()
    stale = c.snapshot()
    c.stop()
    current = c.resume()
    assert current != stale
    with pytest.raises(CommitStopped):
        with c.commit_window(stale):
            pass
    with c.commit_window(current):
        pass


def test_stop_waits_for_active_commit_window():
    c = CommitCoordinator()
    entered, release, stopped = Event(), Event(), Event()
    def writer():
        with c.commit_window(c.snapshot()):
            entered.set()
            assert release.wait(3)
    def stopper():
        c.stop()
        stopped.set()
    t1 = Thread(target=writer)
    t1.start()
    assert entered.wait(3)
    t2 = Thread(target=stopper)
    t2.start()
    assert not stopped.wait(0.05)
    release.set()
    t1.join(3)
    t2.join(3)
    assert stopped.is_set()
    with pytest.raises(CommitStopped):
        with c.commit_window(c.snapshot()):
            pass
