"""
LLM backend abstraction — single call_llm() used by all modules.

Active backend: Mistral free tier (open-mistral-7b) via OpenAI-compatible API.
  Config: OPENAI_BASE_URL + OPENAI_API_KEY in .env

Dormant backend: Ollama (local, no key needed).
  Not usable on macOS 13 Ventura — requires macOS 14+.
  Switch by setting LLM_BACKEND=ollama in .env if on a supported machine.
"""

import time
import requests
import config

# Lazy-init OpenAI client only if needed
_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        )
    return _openai_client


def _call_ollama(system_prompt: str, user_message: str) -> str:
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
            "num_predict": config.LLM_MAX_TOKENS,
        },
    }
    resp = requests.post(
        f"{config.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def _call_openai_compatible(system_prompt: str, user_message: str) -> str:
    client = _get_openai_client()
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
        timeout=120,
    )
    return resp.choices[0].message.content.strip()


def call_llm(system_prompt: str, user_message: str, max_retries: int = 3) -> str:
    """Call the configured LLM backend with retry logic."""
    last_error = None
    for attempt in range(max_retries):
        try:
            if config.LLM_BACKEND == "ollama":
                return _call_ollama(system_prompt, user_message)
            else:
                return _call_openai_compatible(system_prompt, user_message)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  [LLM] Attempt {attempt+1} failed ({e}), retrying in {wait}s...")
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
