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

---

# Task Severity Assessment Protocol

Run before EVERY task. No exceptions. Do not act until user confirms.

## Floor rule

Nothing in this repo is below 🟡 MEDIUM.

## Severity rules

🟡 MEDIUM — single file, low-risk, reversible  
🟠 HIGH — any of: 2+ files, new function/class, touches `evolution.py` / `metrics.py` / `llm.py` / `store.py` / `tools/seed.py` / `tools/registry.py`  
🔴 CRITICAL — any of: `config.py`, `feedback.py`, `benchmark.py`, `tools/registry.json`, `.env`, `runs/`, `state0/`, judge model string, adoption-gate formula  

If confidence is Low → bump one level up.

## Output this block then STOP
╔══ TASK ASSESSMENT ════════════════════╗
Severity  : [🟡/🟠/🔴 + label]
Signals   : [criteria that fired]
Confidence: [High/Medium/Low]
Plan Mode : [ON/OFF]
Thinking  : [think / think hard / ultrathink]
╚═══════════════════════════════════════╝
→ yes | adjust | skip
Do not write any code, read any files, or take any action until the user responds.

## Mode map

🟡 MEDIUM   → Plan OFF | think  
🟠 HIGH     → Plan ON  | think hard  
🔴 CRITICAL → Plan ON  | ultrathink  

## Response handling

- **yes** → proceed with recommended settings
- **adjust** → ask what mode/thinking the user wants, confirm, then proceed
- **skip** → proceed with no plan mode, no extended thinking
- **anything else** → treat as yes

## Examples

"Fix typo in DETAILS_/" → 🟡 MEDIUM  
"Add docstring to a function" → 🟡 MEDIUM  
"Add drift signal to metrics.py" → 🟠 HIGH  
"Refactor generate_population() signature" → 🟠 HIGH  
"Change config.py ADOPT_MARGIN" → 🔴 CRITICAL  
"Edit feedback.py oracle logic" → 🔴 CRITICAL  
"Switch JUDGE_MODEL to another model" → 🔴 CRITICAL