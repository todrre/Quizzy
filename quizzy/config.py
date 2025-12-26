from __future__ import annotations

import os


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

    OPENTDB_TIMEOUT_SECONDS = int(os.environ.get("OPENTDB_TIMEOUT_SECONDS", "5"))
    UPSTASH_TIMEOUT_SECONDS = int(os.environ.get("UPSTASH_TIMEOUT_SECONDS", "5"))

    UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").strip()
    UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "").strip()
    UPSTASH_KEY_PREFIX = os.environ.get("UPSTASH_KEY_PREFIX", "quiz:")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
