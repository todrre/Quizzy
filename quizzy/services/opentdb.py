from __future__ import annotations

import hashlib
import html
import random
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class TriviaQuestion:
    question_id: str
    prompt: str
    choices: list[str]
    correct_answer: str


class OpenTDBError(RuntimeError):
    pass


def fetch_multiple_choice_question(*, timeout_seconds: int) -> TriviaQuestion:
    url = "https://opentdb.com/api.php"
    params = {"amount": 1, "type": "multiple"}

    try:
        res = requests.get(url, params=params, timeout=timeout_seconds)
    except requests.RequestException as exc:
        raise OpenTDBError("OpenTDB request failed") from exc

    if res.status_code != 200:
        raise OpenTDBError(f"OpenTDB returned HTTP {res.status_code}")

    try:
        payload = res.json()
    except ValueError as exc:
        raise OpenTDBError("OpenTDB returned invalid JSON") from exc

    if payload.get("response_code") != 0:
        raise OpenTDBError(f"OpenTDB response_code={payload.get('response_code')}")

    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise OpenTDBError("OpenTDB returned no results")

    item = results[0]
    raw_prompt = item.get("question")
    raw_correct = item.get("correct_answer")
    raw_incorrect = item.get("incorrect_answers")

    if not isinstance(raw_prompt, str) or not isinstance(raw_correct, str) or not isinstance(raw_incorrect, list):
        raise OpenTDBError("OpenTDB result shape unexpected")

    prompt = html.unescape(raw_prompt)
    correct = html.unescape(raw_correct)
    incorrect = [html.unescape(x) for x in raw_incorrect if isinstance(x, str)]

    choices = incorrect + [correct]
    random.shuffle(choices)

    qid_source = "\n".join([prompt, correct, *sorted(incorrect)])
    qid = hashlib.sha256(qid_source.encode("utf-8")).hexdigest()[:16]

    return TriviaQuestion(question_id=qid, prompt=prompt, choices=choices, correct_answer=correct)
