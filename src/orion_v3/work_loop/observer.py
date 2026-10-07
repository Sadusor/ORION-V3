"""Minimal real-time observability projection for the first milestone."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True, slots=True)
class WorkEvent:
    event_type: str
    project_id: str
    task_id: str
    detail: str
    timestamp: str


class WorkObserver:
    """Tiny sink-based observer.  No event bus and no fake model-thought events."""

    def __init__(self, sink: Callable[[WorkEvent], None] | None = None):
        self._sink = sink or (lambda event: None)

    def emit(self, event_type: str, project_id: str, task_id: str, detail: str = "") -> WorkEvent:
        event = WorkEvent(
            event_type=event_type,
            project_id=project_id,
            task_id=task_id,
            detail=detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._sink(event)
        return event
