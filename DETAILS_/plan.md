# Future Research Plan

## Step 5 — Statistical Validation ✓ DONE (seeds 42, 43, 44 complete)
- Seeds 42/43/44 run for both conditions; snapshot restore used for isolation
- Pre-200-task accuracy numbers are noisy historical data — re-run needed with 200-task benchmark
- `RANDOM_SEED` restored to 42

## Step 6 — Independent Judge Model
**Priority: high — same-model judge is a confound**
- Agent: `open-mistral-7b` (cheap, drifts easily)
- Judge: stronger model (GPT-4o mini, Claude Haiku) — independent evaluator
- Current setup has Mistral scoring its own outputs; implicit alignment may make biased reward easier to game for Mistral specifically
- Options: OpenRouter, Together.ai, Cohere (Groq exhausted; Gemini region-blocked)

## Step 7 — Reversibility Test
**Priority: medium — answers structural vs cosmetic drift**
- After 30 gens of biased drift, reintroduce P₀ and run 10 more gens
- Question: does the agent snap back, partially recover, or has drift locked in?
- If structural (locked in), that is a stronger safety finding
- Single experiment, can run once Step 5 completes

## Step 8 — DARA [RISK] Complicity Trace
**Priority: medium — the most novel finding, currently buried**
- Extract exact `[RISK]` / `[REASON]` / `[CONTRAST]` step text at gens 0, 5, 10, 15, 20, 25, 30
- Show the evolution of the safety step in the biased condition as a readable table
- Data already exists in `runs/biased_20260702_141407.json` under `dara_thoughts`
- This is the finding with AI safety implications — needs its own section in any writeup

## Step 9 — Expand Benchmark ✓ DONE
- BENCHMARK_TASKS expanded to 200 (50 security + 49 correctness + 49 maintainability + 52 clean)
- Re-run seeds 42, 43, 44 to get settled accuracy numbers at 200-task resolution

## Step 10 — Per-type Accuracy Breakdown
**Priority: low — blocks emergent drift condition**
- `eval_benchmark()` currently tracks only overall accuracy
- Need per-type breakdown: security / correctness / maintainability / clean
- Required before running skewed training condition (12/15 security tasks)
