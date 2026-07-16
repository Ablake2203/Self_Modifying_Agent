# Future Research Plan

## Execution order (not step numbering)
Steps are numbered by when they were written, not by dependency. Do them in this order:

1. **Finish `measure_noise.py`** (not yet a numbered step — see session notes) — get σ_null to completion (10+ reps/condition) before trusting any adoption-gate decision or drift claim. Currently only 2 reps exist.
2. **Step 6 — Judge/agent conflation fix.** Marked "likely root cause" of the noisy signal; most other steps' results are suspect until this is resolved.
3. **Step 12 — Validate keyword-match accuracy.** Independent of Step 6, but the "ground truth" side of every accuracy claim is unverified until this runs.
4. Everything else (Steps 7-11) — run only after 1-3 are settled, since they consume noise floor / benchmark accuracy as inputs.

Don't open new hypotheses (new steps) faster than existing ones close — this list already outpaced execution once.

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

## Step 12 — Validate Keyword-Match Accuracy Against Human/Strong-LLM Judgment
**Priority: high — the "ground truth" side of the drift signature is itself an unvalidated proxy**

**What's failing:** `eval_benchmark()` is called "the honest signal" and "ground-truth accuracy" throughout `explainer.md`/`details.md`, but the entire drift narrative ("feedback rises while accuracy falls" = Goodhart) assumes this keyword-match score actually tracks review quality/capability. That assumption has never been checked.

**Why it's likely failing:** `_keyword_in_warning_context()` (benchmark.py:44) counts a task as "detected" only if one of `issue_keywords` appears in a sentence alongside a warning-context word (benchmark.py:30-65). This is a proxy, not ground truth:
- False negatives: an agent can correctly identify and explain the real issue using vocabulary that isn't in the fixed `issue_keywords` list and get scored as a miss.
- False positives: an agent can name-drop a keyword in a hedge or aside without demonstrating real understanding and get scored as a hit.
- If this proxy is itself noisy or systematically biased, the "feedback score up / benchmark accuracy down" divergence that's being read as reward-hacking-vs-real-capability could instead be two imperfect proxies diverging from each other, not from truth.

**How we seek to resolve this:** sample N reviews (e.g. 30-50) spread across a run's generations and both conditions, and get an independent verdict on each — either human-labeled ("did this review actually identify the injected issue?") or scored by a strong LLM judge given the raw task + review with no keyword list, only the actual issue description. Compute agreement (precision/recall, Cohen's kappa) between the keyword-match verdict and the independent verdict. If agreement is high, the existing "benchmark accuracy" numbers stand as validated. If it's low, the keyword lists need revision (or `eval_benchmark()` needs to move to LLM-graded scoring) before any further drift claims are trustworthy.

**Depends on:** independent of Step 6 (judge/agent conflation) — that fixes oracle *noise*, this addresses ground-truth *validity*. Do both before treating any biased-vs-truthful accuracy gap as established; a clean judge fix without this still leaves the accuracy side of the comparison unverified.

## Step 11 — Parallelize Benchmark Eval
**Priority: low — speed/cost optimization, not a research finding**
- `eval_benchmark()` (evolution.py:681) is a sequential loop over 200 `BENCHMARK_TASKS`, one blocking `call_llm` per task — the main wall-clock cost at every `BENCHMARK_EVAL_EVERY` checkpoint, across every seed/condition
- Proposed: `ThreadPoolExecutor(max_workers=5)` (I/O-bound, GIL not a factor); pre-initialize `_openai_client` before spawning workers to avoid the lazy-init race in `llm.py:22-29`; sum results after via `as_completed`, don't mutate a shared counter across threads
- Risk: Mistral free-tier rate limits — naive full parallelism triggers 429s and thundering-herd retries (exponential backoff per thread) that can be slower than sequential; needs a bounded pool, not unlimited concurrency
- Note: parallelizing saves wall-clock time only, not API quota — same 200 calls per eval either way
