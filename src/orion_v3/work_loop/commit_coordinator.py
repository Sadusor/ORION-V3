"""In-process STOP/commit ordering primitive.

A STOP request and a commit decision share a lock. This does not provide
cross-process atomicity, OS isolation, or cancellation of committed effects.
"""
from __future__ import annotations
from contextlib import contextmanager
from threading import RLock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .stop import StopSource


class CommitStopped(RuntimeError):
    pass


class CommitCoordinator:
    def __init__(self, stop_source: StopSource | None = None):
        self._stop_source = stop_source
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
            # Fail closed if the authoritative STOP source is unreadable.
            try:
                authoritative_stop = (
                    self._stop_source.stop_requested()
                    if self._stop_source is not None else False
                )
            except Exception as exc:
                raise CommitStopped("authoritative STOP unavailable") from exc
            if authoritative_stop or self._stopped or self._generation != expected_generation:
                raise CommitStopped("STOP or stale generation blocked commit")
            yield
