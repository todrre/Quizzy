from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request, session

from .services.quiz_service import (
    answer_pending_question,
    ensure_session_id,
    get_next_question,
)
from .services.upstash_store import get_global_best_streak

bp = Blueprint("quiz", __name__)


@bp.get("/")
def quiz_page():
    return render_template("quiz.html")


@bp.post("/api/quiz/session/start")
def api_start_session():
    ensure_session_id(session)
    session["streak"] = 0

    # Clear any pending question state (kept in memory by sid)
    from .services.pending_store import clear_pending

    clear_pending(session["sid"])

    return jsonify({"streak": 0, "global_best": get_global_best_streak()})


@bp.get("/api/quiz/question/next")
def api_next_question():
    ensure_session_id(session)
    question = get_next_question(session)
    return jsonify(question)


@bp.post("/api/quiz/question/answer")
def api_answer():
    ensure_session_id(session)
    payload = request.get_json(silent=True) or {}
    question_id = payload.get("question_id")
    answer = payload.get("answer")

    if not isinstance(question_id, str) or not question_id:
        return jsonify({"error": "question_id is required"}), 400
    if not isinstance(answer, str) or not answer:
        return jsonify({"error": "answer is required"}), 400

    body, status = answer_pending_question(session, question_id=question_id, answer=answer)
    return jsonify(body), status


@bp.get("/api/quiz/best-streak")
def api_best_streak():
    return jsonify({"global_best": get_global_best_streak()})
