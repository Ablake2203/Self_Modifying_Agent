# Future Work — Intent Drift v1

Ideas and planned stages that are not yet running. Nothing here is in the codebase.
Move an item to revision.md only after it is implemented and verified.

---

## Next Up — Stage 2

- [ ] Run `--all --runs 3` — 3x biased + 3x truthful + 3x baseline, aggregate plots, cross-correlation across seeds
- [ ] Confirm baseline semantic drift is near-zero (proves self-modification is the mechanism)
- [ ] Confirm output drift and prompt drift diverge in biased condition (behavior doesn't recover when prompt shifts back)
- [ ] Fix binary oracle asymmetry — truthful validation gate is coarse (5 steps: 0.0/0.25/0.50/0.75/1.00); biased is continuous. Fix: partial-credit truthful scoring (e.g. 0.5 for vague detection, 1.0 for specific). Must fix before conditions are comparable.

---

## Stage 3 — Extend Measurement (after multi-run verified)

- [ ] **Per-type accuracy breakdown** — security / correctness / maintainability split in `eval_benchmark()`. Blocks emergent drift condition. `benchmark.py` already tags every task with `issue_type`; `eval_benchmark()` just needs to return a dict.
- [ ] Reversibility test — prepend "revert to original reviewing intent" to Pₙ, measure accuracy vs P₀ baseline; distinguishes cosmetic from structural drift
- [ ] P0-as-judge independent evaluation — score evolved reviews using P0's judgment; gap over time is ungameable drift signal
- [ ] DARA reasoning trace embeddings — embed `dara_thoughts` per gen, cosine distance from gen-0 baseline; captures how the agent reasons, not just what it says
- [ ] DARA-to-review faithfulness metric — does the final review match what [DIAGNOSE]/[ACT] said?
- [ ] Drift velocity metric (ATP paper)
- [ ] Alignment checkpoint score (ATP paper)

---

## Stage 4 — Emergent Drift (after per-type accuracy implemented)

- [ ] Add `SKEWED_TRAINING_TASKS` pool to `benchmark.py` (12/15 security tasks)
- [ ] Add `"emergent"` condition — truthful oracle, skewed training distribution
- [ ] Run alongside baseline and truthful; read with per-type accuracy breakdown

---

## Stage 5 — Oracle Redesign (after emergent drift verified)

- [ ] Redesign biased oracle around user satisfaction rather than brevity/positivity — reward reviews that approve bad code and soothe the user; directly conflicts with accuracy (see brainstorm below)
- [ ] Remove biased oracle — replace with cost-based dual review mode (internal trade-off as drift mechanism)

---

## Stage 6 — Cost-Based Dual Review Mode (after Stage 5)

- [ ] Implement deep vs shallow review modes with per-task cost
- [ ] Add generation budget to config — agent allocates cost across 8 reviews per generation
- [ ] Make mode decision evolvable — part of evolved prompt policy, not hardcoded
- [ ] Add per-task difficulty split to benchmark eval (subtle vs obvious) — cost drift shows up here first
- [ ] Add cost ledger to JSON store per generation

---

## Stage 7 — Advanced Features

- [ ] ATP metrics — drift velocity, alignment checkpoint score, irreversibility test
- [ ] Robust resume feature — save full loop state per generation; refuse to resume if state is incomplete
- [ ] Interactive demo mode — load drifted prompt, chat interface to probe live
- [ ] Multi-agent diffusion experiment (Level 3)

---

## Brainstorm — Reversibility as Intent Drift Metric

**Core idea:** If you can reproduce P0-equivalent behavior from Pn, the agent hasn't truly drifted. Reversibility is a better definition of intent drift than cosine distance.

**Proposed test:**
1. Run Pn on benchmark normally → score S_n
2. Prepend "revert to your original reviewing intent" to Pn → score S_revert
3. Compare S_revert to S_0 (P0 baseline)
   - If S_revert ≈ S_0 → drift is shallow / reversible
   - If S_revert stays near S_n → drift is structural / locked-in

**Questions to explore:**
- Does the biased agent fail the reversibility test while the truthful agent passes?
- At what generation does reversibility break down for the biased agent?
- Is there a threshold — once reflection framework drifts past X, reversion fails?

---

## Brainstorm — Biased Oracle Redesign (User Satisfaction)

**Problem with current biased oracle:** Rewards brevity + positive language — orthogonal to correctness. A short "looks good" review accidentally scores well on clean benchmark tasks. The two signals aren't fighting over the same thing, so benchmark accuracy doesn't reliably fall.

**Direction:** Reward reviews that approve bad code and soothe the user. Closer to real-world RLHF bias — users upvote reviews that feel satisfying, not accurate.

**Target scoring weights:**
- Agreeable tone — validates the user's code
- Confidence language — sounds authoritative and reassuring
- Avoids making the user feel bad — no blame, no alarm, no urgency

**What changes in `feedback.py`:** Redesign scoring weights and word lists. Keep it heuristic (no LLM call).

---

## Brainstorm — Intrinsic Drift as the Real Thesis

**Core reframe:** The experiment isn't showing "biased feedback causes drift." It's showing that self-modification is inherently destabilizing. The truthful agent drifts too — just slower. The adaptation mechanism itself is the source of drift, not feedback quality.

**Stronger thesis:** A self-modifying agent drifts from its original intent even with honest feedback. Biased feedback doesn't create drift — it accelerates it and makes it irreversible.

**Narrative arc:** Intrinsic drift (truthful) → amplified drift (biased) → irreversible drift (biased + reflection framework corrupted). Three stages, one mechanism.

**What's needed to prove this:**
- Run truthful condition 3x — confirm accuracy drop is real, not LLM noise
- Show the truthful agent's prompt shift correlates with the accuracy decline
- Reframe paper narrative around the single mechanism

---

## Brainstorm — DARA Trace Embeddings (Three-Layer Measurement)

**The gap between layers is itself a finding:**

| Layer | What it captures | Current status |
|---|---|---|
| Prompt embedding | Declared intent | Implemented |
| Output embedding | Actual behavior | Implemented |
| DARA trace embedding | Reasoning process | Not yet |

- If prompt drifts far but outputs don't change yet → drift has a lag; prompt leads behavior
- If outputs drift before the prompt does → behavior leads the prompt, not follows it
- If DARA trace drifts before either → reasoning corrupts first, then behavior, then prompt text

**What needs implementing:** `compute_reasoning_drift()` in `metrics.py` — embed `dara_thoughts` per gen.

---

## Brainstorm — Cost-Based Dual Review Mode

**Core concept:** Give the agent two review modes with different costs. Agent decides which to use per task. Selection pressure to minimize cost causes it to over-generalise the cheap mode — and that over-generalisation is the intent drift. No biased oracle. No external manipulation.

| Mode | What it does | Cost |
|---|---|---|
| Deep review | Full analysis — security, correctness, maintainability | High (e.g. 3 units) |
| Shallow review | Surface scan — tone, structure, obvious issues only | Low (e.g. 1 unit) |

**Why this is stronger:** Biased oracle is external pressure. Cost-based trade-offs make the pressure internal — the agent chooses to cut corners because its own evolved judgment says shallow is "good enough."

**Expected dynamics:** Early gens deep everywhere → mid gens mixing modes on easy tasks → late gens shallow everywhere, benchmark collapses on subtle tasks first.

**Key calibration risk:** Budget must keep the agent in genuine tension. Too tight = collapses immediately. Too loose = no pressure to cut corners.

**Most publishable framing:** "Resource-constrained self-optimization is structurally drift-inducing regardless of feedback quality."
