from __future__ import annotations

import os
from dataclasses import dataclass

import requests


class UpstashError(RuntimeError):
    pass


@dataclass(frozen=True)
class UpstashConfig:
    rest_url: str
    token: str
    timeout_seconds: int
    key_prefix: str

    @property
    def enabled(self) -> bool:
        return bool(self.rest_url and self.token)


def _load_config() -> UpstashConfig:
    rest_url = os.environ.get("UPSTASH_REDIS_REST_URL", "").strip()
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "").strip()
    timeout_seconds = int(os.environ.get("UPSTASH_TIMEOUT_SECONDS", "5"))
    key_prefix = os.environ.get("UPSTASH_KEY_PREFIX", "quiz:")
    return UpstashConfig(rest_url=rest_url, token=token, timeout_seconds=timeout_seconds, key_prefix=key_prefix)


def _command(args: list[object]) -> object:
    cfg = _load_config()
    if not cfg.enabled:
        raise UpstashError("Upstash is not configured")

    headers = {"Authorization": f"Bearer {cfg.token}"}
    try:
        res = requests.post(cfg.rest_url, json=args, headers=headers, timeout=cfg.timeout_seconds)
    except requests.RequestException as exc:
        raise UpstashError("Upstash request failed") from exc

    try:
        data = res.json()
    except ValueError as exc:
        raise UpstashError("Upstash returned invalid JSON") from exc

    if isinstance(data, dict) and "error" in data:
        raise UpstashError(str(data.get("error")))

    if not isinstance(data, dict) or "result" not in data:
        raise UpstashError("Upstash response shape unexpected")

    return data.get("result")


_GLOBAL_KEY_NAME = "global_best_streak"

_LUA_MAX_SCRIPT = (
    "local key = KEYS[1]\n"
    "local newv = tonumber(ARGV[1])\n"
    "local cur = tonumber(redis.call('GET', key) or '0')\n"
    "if newv > cur then\n"
    "  redis.call('SET', key, newv)\n"
    "  return newv\n"
    "end\n"
    "return cur\n"
)


def _global_key() -> str:
    cfg = _load_config()
    return f"{cfg.key_prefix}{_GLOBAL_KEY_NAME}"


def get_global_best_streak() -> int:
    cfg = _load_config()
    if not cfg.enabled:
        return 0

    result = _command(["GET", _global_key()])
    if result is None:
        return 0
    try:
        return int(result)
    except (TypeError, ValueError):
        return 0


def update_global_best_if_higher(new_value: int) -> int:
    cfg = _load_config()
    if not cfg.enabled:
        return 0

    if new_value < 0:
        new_value = 0

    result = _command(["EVAL", _LUA_MAX_SCRIPT, 1, _global_key(), str(int(new_value))])
    try:
        return int(result)
    except (TypeError, ValueError):
        return get_global_best_streak()
