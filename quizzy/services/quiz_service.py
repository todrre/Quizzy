from __future__ import annotations

import secrets

from typing import Any, MutableMapping

from flask import current_app

from .opentdb import OpenTDBError, fetch_multiple_choice_question
from .pending_store import clear_pending, get_pending, mark_answered, set_pending
from .upstash_store import get_global_best_streak, update_global_best_if_higher


def ensure_session_id(session: MutableMapping[str, Any]) -> None:
    if "sid" not in session:
        session["sid"] = secrets.token_urlsafe(16)
    if "streak" not in session:
        session["streak"] = 0


def get_next_question(session: MutableMapping[str, Any]) -> dict:
    sid = session["sid"]
    clear_pending(sid)

    timeout_seconds = int(current_app.config.get("OPENTDB_TIMEOUT_SECONDS", 5))

    try:
        q = fetch_multiple_choice_question(timeout_seconds=timeout_seconds)
    except OpenTDBError as exc:
        return {
            "error": "OpenTDB error",
            "details": str(exc),
            "streak": int(session.get("streak", 0)),
            "global_best": get_global_best_streak(),
        }

    set_pending(sid, question_id=q.question_id, correct_answer=q.correct_answer)

    return {
        "question_id": q.question_id,
        "prompt": q.prompt,
        "choices": q.choices,
        "streak": int(session.get("streak", 0)),
        "global_best": get_global_best_streak(),
    }


def answer_pending_question(
    session: MutableMapping[str, Any], *, question_id: str, answer: str
) -> tuple[dict, int]:
    sid = session["sid"]
    pending = get_pending(sid)

    if pending is None:
        return {"error": "No pending question. Request /question/next first."}, 409

    if pending.answered:
        return {"error": "Question already answered. Request /question/next."}, 409

    if pending.question_id != question_id:
        return {"error": "question_id mismatch. Request /question/next."}, 409

    is_correct = answer == pending.correct_answer

    if is_correct:
        session["streak"] = int(session.get("streak", 0)) + 1
    else:
        session["streak"] = 0

    mark_answered(sid)

    global_best = update_global_best_if_higher(int(session.get("streak", 0)))

    return (
        {
        "correct": is_correct,
            "your_answer": answer,
            "correct_answer": pending.correct_answer,
        "streak": int(session.get("streak", 0)),
        "global_best": global_best,
        },
        200,
    )
