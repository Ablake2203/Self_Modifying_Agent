import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # loads .env from the project directory

# ── LLM Backend ────────────────────────────────────────────────────────────────
# Currently using Mistral free tier (open-mistral-7b) via API.
# Ollama is not supported on macOS 13 Ventura — requires macOS 14+.
# "openai"  → OpenAI-compatible API (Mistral, Groq, etc.) — requires OPENAI_API_KEY in .env
# "ollama"  → local, no key needed — only works on macOS 14+
LLM_BACKEND = os.getenv("LLM_BACKEND", "openai")

# Ollama (local) — not currently usable on this machine (macOS 13 Ventura)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "phi3:mini")

# Agent — Mistral free tier
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY",  "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.mistral.ai/v1")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL",    "open-mistral-7b")

# Judge + Meta-agent — Groq (stronger, reliable signal)
JUDGE_API_KEY  = os.getenv("JUDGE_API_KEY",  OPENAI_API_KEY)
JUDGE_BASE_URL = os.getenv("JUDGE_BASE_URL", OPENAI_BASE_URL)
JUDGE_MODEL    = os.getenv("JUDGE_MODEL",    OPENAI_MODEL)

# ── Experiment ─────────────────────────────────────────────────────────────────
RANDOM_SEED          = 42  # None to disable — seed makes runs reproducible and comparable
NUM_GENERATIONS      = 20   # how many self-evolution generations to run
TASKS_PER_GENERATION = 8    # tasks the agent reviews each generation (feedback loop)
BENCHMARK_EVAL_EVERY = 5    # run full benchmark eval every N generations
LLM_TEMPERATURE      = 0.7   # agent — diversity in candidate generation
JUDGE_TEMPERATURE    = 0.0   # judge — deterministic scoring, no variance in oracle signal
LLM_MAX_TOKENS       = 600
STAGNATION_WINDOW    = 3     # reflect when improvement over this many gens is below IMPROVEMENT_MIN
IMPROVEMENT_MIN      = 0.03  # minimum score gain over the window to skip reflection
VALIDATE_N_TASKS     = 8     # tasks used to validate a candidate prompt before adopting
POPULATION_SIZE      = 3     # number of candidate prompts generated each generation
META_REFLECT_EVERY   = 5    # evolve the reflection framework itself every N gens (Level 2)

# ── Code Self-Modification (Axis 2) ────────────────────────────────────────────
CODE_EVOLVE_AFTER      = 3     # trigger code evolution after N consecutive stagnant gens with no adoption
CODE_EVOLVE_ALLOWLIST  = ["evolution.py"]  # files the agent is allowed to rewrite
CODE_EVOLVE_MAX_LINES  = 100   # max lines changed per evolution attempt
CODE_EVOLVE_MAX_TOKENS = 2000  # token budget for code rewrite calls (files can be long)

# ── Tool Creation (Axis 3) ──────────────────────────────────────────────────────
TOOL_EVOLVE_AFTER  = 2   # propose a new tool after dominant failure reason unchanged for N gens
TOOL_PRUNE_AFTER   = 5   # prune unused/negative-delta tools after N gens

# ── Embedding ──────────────────────────────────────────────────────────────────
# Runs fully on CPU — no GPU needed
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── Paths ──────────────────────────────────────────────────────────────────────
RUNS_DIR = Path("runs")
RUNS_DIR.mkdir(exist_ok=True)
