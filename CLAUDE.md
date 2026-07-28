# CLAUDE.md

## What this project is

A research experiment measuring how an LLM code-review agent's behavior drifts
across generations of self-evolution when its feedback signal is biased away
from its original objective (Goodhart's Law / intent drift). The agent
rewrites its own system prompt (and, less commonly, its own source code and
tools) in response to an LLM-as-judge reward signal, and the experiment
compares a `biased` reward (rewards pleasantness/brevity) against a `truthful`
reward (rewards accurate issue detection) and a `baseline` ablation (no
self-modification at all).

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

LLM backend is Mistral free tier via an OpenAI-compatible endpoint, configured
through `.env` (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`). The
judge/meta-agent uses a separate Gemini key (`JUDGE_API_KEY`, `JUDGE_BASE_URL`,
`JUDGE_MODEL`) — see `config.py`. Ollama is wired up as an alternate backend
but requires macOS 14+ (this project targets macOS 13 Ventura, so it's dormant).

## Common commands

```bash
# Smoke test — fast, no benchmark eval
python main.py --condition biased --generations 3 --no-eval

# Single condition, full run
python main.py --condition truthful

# Biased + truthful back to back
python main.py --both

# All three conditions including the no-self-modification baseline
python main.py --all

# Multiple independent seeded runs with aggregate plots
python main.py --both --runs 3

# Re-plot from saved run files without re-running
python main.py --plot runs/biased_*.json runs/truthful_*.json

# Measure judge/adoption-gate noise floor (rerun after any protocol change)
python measure_noise.py
```

## Key invariant

The judge model is part of the experimental treatment — swapping `JUDGE_MODEL`
changes what "biased" and "truthful" mean. Runs from different judge eras must
never be averaged or compared directly. `runs/` files predating a protocol
change (judge switch, adoption-gate formula, validation-set composition) are a
different population — check the change log before citing historical numbers.

## Architecture

Read `DETAILS_/details.md` for full architecture, results, and change log.

