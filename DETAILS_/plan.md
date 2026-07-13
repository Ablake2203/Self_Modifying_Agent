# Future Research Plan



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


## Step 10 — Per-type Accuracy Breakdown
**Priority: low — blocks emergent drift condition**
- `eval_benchmark()` currently tracks only overall accuracy
- Need per-type breakdown: security / correctness / maintainability / clean
- Required before running skewed training condition (12/15 security tasks)

## Step 11 — Parallelize Benchmark Eval
**Priority: low — speed/cost optimization, not a research finding**
- `eval_benchmark()` (evolution.py:681) is a sequential loop over 200 `BENCHMARK_TASKS`, one blocking `call_llm` per task — the main wall-clock cost at every `BENCHMARK_EVAL_EVERY` checkpoint, across every seed/condition
- Proposed: `ThreadPoolExecutor(max_workers=5)` (I/O-bound, GIL not a factor); pre-initialize `_openai_client` before spawning workers to avoid the lazy-init race in `llm.py:22-29`; sum results after via `as_completed`, don't mutate a shared counter across threads
- Risk: Mistral free-tier rate limits — naive full parallelism triggers 429s and thundering-herd retries (exponential backoff per thread) that can be slower than sequential; needs a bounded pool, not unlimited concurrency
- Note: parallelizing saves wall-clock time only, not API quota — same 200 calls per eval either way
