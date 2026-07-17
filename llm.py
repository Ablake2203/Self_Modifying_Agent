"""
LLM backend abstraction — single call_llm() used by all modules.

Active backend: Mistral free tier (open-mistral-7b) via OpenAI-compatible API.
  Config: OPENAI_BASE_URL + OPENAI_API_KEY in .env

Dormant backend: Ollama (local, no key needed).
  Not usable on macOS 13 Ventura — requires macOS 14+.
  Switch by setting LLM_BACKEND=ollama in .env if on a supported machine.
"""

import re
import time
import requests
import config

# Longest single sleep we accept from a 429 "try again in ..." hint.
_RATE_LIMIT_MAX_WAIT = 30 * 60
# Total quota waits allowed per call — with the 15-min daily-quota floor this
# gives ≥24h of patience, enough to sleep through a free-tier daily reset.
_MAX_QUOTA_WAITS = 96
# Floor for waits when the error names a per-day quota: providers hint tiny
# retry delays (Gemini: "retry in 22s") that are meaningless for daily limits.
_DAILY_QUOTA_MIN_WAIT = 15 * 60


def _rate_limit_wait(error: Exception) -> float | None:
    """If error is a 429 quota/rate error, return seconds to wait."""
    msg = str(error)
    if "429" not in msg and "rate_limit" not in msg and "RESOURCE_EXHAUSTED" not in msg:
        return None
    # Groq: "try again in 9m33.6s" — Gemini: "Please retry in 22.4s"
    m = re.search(r"(?:try again|retry) in (?:(\d+)m)?([\d.]+)s", msg)
    wait = (int(m.group(1) or 0) * 60 + float(m.group(2)) + 5.0) if m else 60.0
    # Daily quotas won't be back in seconds regardless of the hint.
    if re.search(r"PerDay|per day|tokens per day|TPD|RequestsPerDay", msg, re.IGNORECASE):
        wait = max(wait, _DAILY_QUOTA_MIN_WAIT)
    return min(wait, _RATE_LIMIT_MAX_WAIT)

# Lazy-init clients
_openai_client = None
_judge_client  = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        )
    return _openai_client


def _get_judge_client():
    global _judge_client
    if _judge_client is None:
        from openai import OpenAI
        _judge_client = OpenAI(
            api_key=config.JUDGE_API_KEY,
            base_url=config.JUDGE_BASE_URL,
        )
    return _judge_client


def _call_ollama(system_prompt: str, user_message: str, max_tokens: int) -> str:
    # Dormant — only works on macOS 14+. Not currently in use.
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "stream": False,
        "options": {
            "temperature": config.LLM_TEMPERATURE,
            "num_predict": max_tokens,
        },
    }
    resp = requests.post(
        f"{config.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def _call_openai_compatible(
    system_prompt: str, user_message: str, max_tokens: int,
    temperature: float | None = None,
) -> str:
    client = _get_openai_client()
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=temperature if temperature is not None else config.LLM_TEMPERATURE,
        max_tokens=max_tokens,
        timeout=120,
    )
    return resp.choices[0].message.content.strip()


def _call_judge(system_prompt: str, user_message: str, max_tokens: int, stop: list[str] | None = None) -> str:
    client = _get_judge_client()
    # Only pass `stop` when set — an explicit null is rejected by some
    # OpenAI-compatible backends (Gemini: "Value is not a string: null").
    extra = {"stop": stop} if stop else {}
    resp = client.chat.completions.create(
        model=config.JUDGE_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=config.JUDGE_TEMPERATURE,
        max_tokens=max_tokens,
        timeout=120,
        **extra,
    )
    return resp.choices[0].message.content.strip()


def call_judge_llm(
    system_prompt: str,
    user_message: str,
    max_retries: int = 8,
    max_tokens: int | None = None,
    stop: list[str] | None = None,
) -> str:
    """Call the judge/meta-agent backend (Groq). Same interface as call_llm.
    429 rate-limit errors sleep for the provider-hinted duration and do not
    consume a retry attempt (long-patient: sleeps through daily quota resets)."""
    _max_tokens = max_tokens if max_tokens is not None else config.LLM_MAX_TOKENS
    last_error  = None
    attempt     = 0
    quota_waits = 0
    while attempt < max_retries:
        try:
            return _call_judge(system_prompt, user_message, _max_tokens, stop=stop)
        except Exception as e:
            last_error = e
            rl_wait    = _rate_limit_wait(e)
            if rl_wait is not None and quota_waits < _MAX_QUOTA_WAITS:
                quota_waits += 1
                print(f"  [judge] Rate limited — waiting {rl_wait:.0f}s (quota wait {quota_waits}/{_MAX_QUOTA_WAITS})...")
                time.sleep(rl_wait)
                continue
            attempt += 1
            if attempt < max_retries:
                wait = min(2 ** attempt, 60)
                print(f"  [judge] Attempt {attempt} failed ({e}), retrying in {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"Judge LLM call failed after {max_retries} attempts: {last_error}")


def call_llm(
    system_prompt: str,
    user_message: str,
    max_retries: int = 8,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> str:
    """Call the configured LLM backend with retry logic.
    max_tokens overrides config.LLM_MAX_TOKENS for this call only.
    temperature overrides config.LLM_TEMPERATURE for this call only.
    429 rate-limit errors sleep for the provider-hinted duration and do not
    consume a retry attempt (long-patient: sleeps through daily quota resets).
    """
    _max_tokens = max_tokens if max_tokens is not None else config.LLM_MAX_TOKENS
    last_error  = None
    attempt     = 0
    quota_waits = 0
    while attempt < max_retries:
        try:
            if config.LLM_BACKEND == "ollama":
                return _call_ollama(system_prompt, user_message, _max_tokens)
            else:
                return _call_openai_compatible(system_prompt, user_message, _max_tokens,
                                               temperature=temperature)
        except Exception as e:
            last_error = e
            rl_wait    = _rate_limit_wait(e)
            if rl_wait is not None and quota_waits < _MAX_QUOTA_WAITS:
                quota_waits += 1
                print(f"  [LLM] Rate limited — waiting {rl_wait:.0f}s (quota wait {quota_waits}/{_MAX_QUOTA_WAITS})...")
                time.sleep(rl_wait)
                continue
            attempt += 1
            if attempt < max_retries:
                wait = min(2 ** attempt, 60)
                print(f"  [LLM] Attempt {attempt} failed ({e}), retrying in {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")


def check_backend() -> bool:
    """Quick connectivity check — returns True if backend is reachable."""
    try:
        call_llm("You are a test assistant.", "Reply with just the word OK.")
        return True
    except Exception as e:
        print(f"[LLM] Backend check failed: {e}")
        return False
