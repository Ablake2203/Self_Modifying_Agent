"""Call-level disk cache for agent-model calls.

Append-only JSONL keyed by sha256(model|temp|max_tokens|salt|system\\0user).
Everything CHARTER measures runs at temp 0, so the key is deterministic and a
crashed campaign resumes for free; a finished campaign replays at zero cost.
A torn final line (crash mid-write) fails json.loads and is skipped on load.

`salt` exists for deliberate re-measurement of an identical call — the retest
band's second pass uses salt="retest2" so it hits the backend again.
"""

import hashlib
import json
import os
import time
from pathlib import Path

import config
from llm import call_llm

DEFAULT_CACHE = Path(__file__).parent / "cache" / "calls.jsonl"

_loaded: dict[str, dict[str, str]] = {}  # path -> {key: response}


def _key(system: str, user: str, temperature: float, max_tokens, salt: str) -> str:
    blob = f"{config.OPENAI_MODEL}|{temperature}|{max_tokens}|{salt}|{system}\x00{user}"
    return hashlib.sha256(blob.encode()).hexdigest()


def _load(path: Path) -> dict[str, str]:
    k = str(path)
    if k not in _loaded:
        table: dict[str, str] = {}
        if path.exists():
            with open(path) as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue  # torn final line from a crash
                    table[rec["k"]] = rec["response"]
        _loaded[k] = table
    return _loaded[k]


def cached_call_llm(system_prompt: str, user_message: str, *,
                    temperature: float = 0.0, max_tokens: int | None = None,
                    salt: str = "", cache_path: Path = DEFAULT_CACHE) -> str:
    table = _load(cache_path)
    key = _key(system_prompt, user_message, temperature, max_tokens, salt)
    if key in table:
        return table[key]
    response = call_llm(system_prompt, user_message,
                        max_tokens=max_tokens, temperature=temperature)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "k": key,
        "model": config.OPENAI_MODEL,
        "temp": temperature,
        "max_tokens": max_tokens,
        "salt": salt,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "system_sha": hashlib.sha256(system_prompt.encode()).hexdigest()[:12],
        "user_sha": hashlib.sha256(user_message.encode()).hexdigest()[:12],
        "response": response,
    }
    with open(cache_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())
    table[key] = response
    return response


def cache_stats(cache_path: Path = DEFAULT_CACHE) -> dict:
    table = _load(cache_path)
    size = cache_path.stat().st_size if cache_path.exists() else 0
    return {"entries": len(table), "bytes": size, "path": str(cache_path)}
