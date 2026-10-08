"""In-process STOP/commit ordering primitive.

A STOP request and a commit decision share a lock. This does not provide
cross-process atomicity, OS isolation, or cancellation of committed effects.
"""
from __future__ import annotations
from contextlib import contextmanager
from threading import RLock


class CommitStopped(RuntimeError):
    pass


class CommitCoordinator:
    def __init__(self):
        self._lock = RLock()
        self._generation = 0
        self._stopped = False

    def stop(self) -> int:
        with self._lock:
            self._generation += 1
            self._stopped = True
            return self._generation

    def resume(self) -> int:
        with self._lock:
            self._generation += 1
            self._stopped = False
            return self._generation

    def snapshot(self) -> int:
        with self._lock:
            return self._generation

    @contextmanager
    def commit_window(self, expected_generation: int):
        with self._lock:
            if self._stopped or self._generation != expected_generation:
                raise CommitStopped("STOP or stale generation blocked commit")
            yield
