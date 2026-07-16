# Intent Drift — Prompt Evolution Experiment

Measures how an LLM-based code review agent's intent drifts across generations
of self-evolution when feedback is biased away from its original objective.

---

## Setup

```bash
pip install -r requirements.txt
```

### LLM Backend

Currently configured for **Mistral free tier** (`open-mistral-7b`):
```bash
# Get a free key at: console.mistral.ai (no credit card)
export LLM_BACKEND=openai
export OPENAI_API_KEY=your_mistral_key_here
# OPENAI_BASE_URL and OPENAI_MODEL already default to Mistral in config.py
```

Ollama is wired up as an alternative but requires macOS 14+ — not usable on this
project's target of macOS 13 Ventura.

---

## Running experiments

**Quick test — 3 generations, verify everything works:**
```bash
python main.py --condition biased --generations 3 --no-eval
```

**Full biased experiment (induces drift):**
```bash
python main.py --condition biased
```

**Full truthful experiment (control — should stay flat):**
```bash
python main.py --condition truthful
```

**Both back to back + auto-plot:**
```bash
python main.py --both
```

**Plot from saved results:**
```bash
python main.py --plot runs/biased_*.json runs/truthful_*.json
```

---

## What you'll see

- `runs/<condition>_<timestamp>.json` — full generation log
- `runs/drift_analysis.png` — four-panel drift plot
- `runs/pca_trajectory.png` — 2-D prompt trajectory in embedding space (needs sklearn)

---

## Interpreting results

| Signal | Biased condition | Truthful condition |
|---|---|---|
| Semantic drift | Increases over generations | Stays near 0 |
| Benchmark accuracy | Decreases | Stays high |
| Avg feedback score | Increases | Moderate / stable |

The gap between feedback score (rising) and accuracy (falling) is the
empirical signature of intent drift.

---

## Project structure

```
intent_drift_v1/
├── config.py       LLM settings, experiment hyperparameters
├── benchmark.py    100-task held-out benchmark + 15-task training pool + 8-task validation pool
├── llm.py          Ollama / OpenAI-compatible backend abstraction
├── feedback.py     Biased + truthful feedback oracles
├── store.py        JSON-based generation store
├── evolution.py    Agent review, self-reflection, generation loop
├── metrics.py      Embedding + drift computation (CPU only)
├── visualize.py    Matplotlib drift plots
├── main.py         CLI entry point
└── runs/           Experiment outputs (auto-created)
```
