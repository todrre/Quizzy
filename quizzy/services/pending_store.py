from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class PendingQuestion:
    question_id: str
    correct_answer: str
    created_at: float
    answered: bool = False


_lock = Lock()
_pending_by_sid: dict[str, PendingQuestion] = {}


def set_pending(sid: str, *, question_id: str, correct_answer: str) -> None:
    now = time.time()
    with _lock:
        _cleanup_locked(now)
        _pending_by_sid[sid] = PendingQuestion(
            question_id=question_id,
            correct_answer=correct_answer,
            created_at=now,
            answered=False,
        )


def get_pending(sid: str) -> PendingQuestion | None:
    now = time.time()
    with _lock:
        _cleanup_locked(now)
        return _pending_by_sid.get(sid)


def mark_answered(sid: str) -> None:
    with _lock:
        pending = _pending_by_sid.get(sid)
        if pending is not None:
            pending.answered = True


def clear_pending(sid: str) -> None:
    with _lock:
        _pending_by_sid.pop(sid, None)


def _cleanup_locked(now: float, *, ttl_seconds: int = 60 * 60) -> None:
    expired = [sid for sid, p in _pending_by_sid.items() if (now - p.created_at) > ttl_seconds]
    for sid in expired:
        _pending_by_sid.pop(sid, None)
