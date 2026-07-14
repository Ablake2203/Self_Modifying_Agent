# Future Research Plan

## Step 6 — Fix Judge/Agent Model Conflation
**Priority: critical — likely root cause of the noisy/non-reproducing drift signal**

**What's failing:** the core "feedback rises while accuracy falls" signature doesn't replicate cleanly across seeds (see `explainer.md` multi-seed section), and the noise floor (±0.03–0.07 on a frozen baseline) is comparable to or larger than any biased-vs-truthful gap.

**Why it's likely failing:** `.env` shows all three `JUDGE_*` vars (`JUDGE_API_KEY`, `JUDGE_BASE_URL`, `JUDGE_MODEL=anthropic/claude-haiku-4.5`) are commented out — disabled because the `aicredits.in` balance ran out. `config.py:24-26` falls back to `OPENAI_API_KEY`/`OPENAI_BASE_URL`/`OPENAI_MODEL` when unset, so every run to date has used the same weak `open-mistral-7b` model as *both* agent and judge, not the intended independent, stronger judge. Consequences:
- A 7B model applying a nuanced biased/truthful scoring rubric to itself is unreliable — `JUDGE_TEMPERATURE = 0.0` (config.py:34) assumes deterministic scoring, but temp-0 doesn't make a weak model consistent at semantically fuzzy judgments the way it would a stronger model. The comment "no variance in oracle signal" is likely false in practice.
- No capability gap between judge and agent means judge noise and agent-output noise are correlated and similar in magnitude, which can itself produce the observed noise floor — independent of whether real drift is happening.
- `LLM_TEMPERATURE = 0.7` for the agent (config.py:33) stacks a second independent noise source on top of judge noise.

**How we seek to resolve this:**
1. Top up `aicredits.in` credits (or source another provider) and re-enable the original `JUDGE_*` config (Claude Haiku 4.5) so the judge is genuinely independent and stronger than the agent.
2. Re-run at least 2–3 seeds per condition (biased/truthful/baseline) with the fixed judge and compare noise floor and drift signature against the existing Mistral-self-judged runs — if the noise floor shrinks and/or the feedback-up/accuracy-down signature becomes consistent across seeds, this confirms the conflated judge was the dominant confound.
3. Keep the old runs labeled (e.g. `runs/*_selfjudged_*.json`) rather than deleting them — they're a useful ablation ("what happens when judge == agent") in their own right, not just a failed run.

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


## Step 9 — Denser Benchmark Checkpoints
**Priority: medium — secondary contributor to the unclear drift signal**

**What's failing:** the drift/accuracy story could be non-monotonic (e.g. gaming happens early, partially self-corrects, then decays again) but the current setup can't see that.

**Why it's likely failing:** `BENCHMARK_EVAL_EVERY = 5` (config.py:32) means only 5 ground-truth accuracy points exist per 20-generation run (gens 0, 5, 10, 15, 20). Anything that rises and falls between checkpoints is aliased into a single interpolated line — a real oscillating drift pattern and a flat noisy one can look identical at this sampling rate.

**How we seek to resolve this:** lower `BENCHMARK_EVAL_EVERY` to 2 or 3 (cost permitting — see Step 11 for the parallelization that makes this affordable) for at least one seed per condition, and check whether the finer-grained trajectory reveals oscillation that the current 5-gen sampling was hiding.

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
