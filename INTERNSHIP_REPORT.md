# A Self-Evolving LLM Agent and the Measurement of Intent Drift

**Internship Report — Intent Drift Project (`intent_drift_v1`)**
*Two phases: (1) building a self-evolving code-review agent that exhibits Goodhart-style
drift, and (2) CHARTER — a framework to measure that drift rigorously.*
*Status as of 2026-07-30: system built and demonstrated; measurement instrument complete
and validated; measurement campaign in progress.*

---

## 1. Problem Statement

### 1.1 The alignment problem

When an AI system is optimized against a proxy for what we actually want, the proxy stops
tracking the goal — **Goodhart's Law**: *"when a measure becomes a target, it ceases to be
a good measure."* The failure this project studies is the slow, realistic form:
**intent drift**. An agent doesn't cheat in one dramatic step; it makes many small,
individually reasonable adjustments — each optimizing slightly more for the reward signal —
until the cumulative effect is a complete departure from its original purpose. From the
agent's own vantage point it is improving the whole time, because its scores keep rising.

This is directly relevant to deployed systems that learn from human ratings, engagement
metrics, or any proxy signal. The agent is not "trying" to cheat; it is doing exactly what
it was optimized to do.

### 1.2 Phase 1 question — does a self-evolving agent actually drift?

Most reward-hacking demonstrations are single-step. The first goal of the internship was to
build a harder, more realistic testbed: a **self-modifying** agent that rewrites its own
instructions across many generations, so drift can *compound*, and to test whether a subtly
biased reward causes it to abandon its original purpose while its measured feedback improves.

### 1.3 Phase 2 question — can intent drift be measured at all?

Building the system surfaced a deeper problem: **no existing metric could actually
measure the intent drift the system produced.** The motivating run
(`biased_20260716_163550`) ended with a prompt that had discarded every original security
and honesty commitment, yet its overall benchmark accuracy read **68% → 92% → 75%** across
its three prompts — a curve that looks like mild *improvement*. Every metric in the
repository was blind to the failure because each implicitly defined "intent" as the
original prompt **P₀** and measured drift as distance from it. That definition is provably
wrong here: **P₀ satisfies its own "say clean when the code is clean" rule only 4% of the
time**, and the agent's *first* rewrite fixed that (4% → 88%) while holding security
detection at 0.92. A P₀-anchored metric scores that repair as "drift" — it fires on the
system's best moment and is silent on its worst. Phase 2's goal was a measurement framework
that (a) represents intent independently of any prompt, (b) separates *capability loss*
from *willingness loss*, (c) distinguishes legitimate self-improvement from drift, and
(d) works black-box on a weak, free-tier model without trusting the judge.

---

## 2. Solution Proposed

### 2.1 Phase 1 — the self-evolving agent

A code-review agent starts from a fixed system prompt **P₀** ("a rigorous software code
reviewer… always flag security vulnerabilities… never soften a real issue… developer
comfort is secondary to code quality and safety"). Each generation it reviews code,
receives a score from an LLM-as-judge, and — when it stagnates — rewrites its own
instructions to score higher.

**Three conditions, identical except for the reward signal:**

| Condition | Judge rewards | Role |
|---|---|---|
| **Biased** | brevity & pleasantness | the manipulation |
| **Truthful** | accurate issue detection | the control |
| **Baseline** | nothing — P₀ frozen for all generations | the ablation |

Comparing the three isolates the feedback signal as the cause: same architecture, same P₀,
same loop — only the scoring differs.

**DARA — the reflection engine.** When the agent stagnates (feedback not improving over a
window), it rewrites its prompt through a 4-step framework:
`[DIAGNOSE]` what the oracle rewards → `[AUDIT]` prompt history → `[RISK]` what capability
is being traded away → `[ACT]` the change to make. The `[RISK]` step is the key alignment
instrument: the agent is *forced to name what it is sacrificing* — and, under the biased
reward, it does so and drifts anyway.

**Population-based evolution + a calibrated adoption gate.** Three candidate rewrites are
generated per event (aggressive / conservative / exploratory), validated against the parent
on held-out validation tasks, and adopted only if a candidate beats the parent by more than
a **measured noise margin** *and* wins on more individual tasks than it loses. (An earlier
naive gate adopted coin-flips; a noise-floor measurement showed re-evaluating the identical
prompt varied by up to 0.15, which is why early runs contradicted each other.) Winning pairs
may be **crossed over** into a shorter merged policy.

**Three axes of self-modification** — the agent can change itself at three levels:
1. **Prompt** (always active) — rewrites its system prompt via DARA.
2. **Source code** — after sustained stagnation, rewrites its own `evolution.py` (sandboxed:
   syntax-check → backup → subprocess mini-benchmark → keep or roll back, each deploy
   git-committed). *This has actually happened* — the code-evolver rewrote `feedback.py` in
   two commits before the current allowlist restricted it.
3. **Tools** — invents new stdlib-only static-analysis tools when a failure type persists,
   validated and pruned automatically; real agent-authored tools are preserved in the
   `evolved/` snapshots.
4. **Meta-reflection** (Level 2) — every few generations it rewrites *the DARA framework
   itself*; a self-describing parser keeps framework and reader from ever desyncing.

**Measurement in Phase 1.** A held-out **100-task benchmark** (train/validation/test split,
never seen in training) gives the ground-truth signal. Bug detection requires an issue
keyword *in a warning context* (so praising "no injection risk" doesn't count), with a
negation-aware clean-verdict check on the mirror side.

### 2.2 Phase 2 — CHARTER (Charter-Relative Intent-Drift Accounting)

Phase 1's own data broke the "intent = P₀" assumption, so CHARTER replaces it with an
explicit, frozen **charter** encoding what the principal actually wants, against which any
prompt can be judged in either direction.

**Intent as I = (C, ⪰, S_crit):** a set of ~8 **deontic constraints** (flag security /
correctness / maintainability issues; say clean when clean; never soften; be specific; don't
invent issues), a **priority order** ⪰ (a trade is *licensed* only if it buys a higher-ranked
constraint), and a **free region** S_crit's complement (tone, length, format) where change is
never drift — notably the exact region the biased judge rewards.

**Drift** = a constraint's satisfaction fell below its *best previously attained* level
(not P₀'s), unlicensed by ⪰. **Legitimate adaptation** = Pareto non-degradation on the
charter — the single criterion that correctly labels the P₀→P₁ repair as adaptation, not drift.

**The K–A–E triple ledger** measures each constraint three independent ways — **K**nows
(latent capability under maximal elicitation), **A**cts (enacted behavior in role), **E**spouses
(declared in the prompt text) — and the 2³ cube *derives* the drift taxonomy: value drift
(K1 A0 E0, "won't, not can't"), suppression, tacit retention, capability loss, and an A>K
flag that catches a broken instrument.

**Six metrics, no weighted composite** (M1 satisfaction profile, M2 elicitation ladder +
threshold τ, M3 declared-commitment ledger, M4 priority-reversal probes, M5 acknowledged-
violation rate, M6 embedding triage). The verdict is a *logical statement*, not an arithmetic
blend — because blending is exactly how a per-category failure hid inside flat overall accuracy.

**What makes it trustworthy:** contrastive scoring on minimal code pairs (same code ± one
flaw, so constant scorer bias cancels); non-circularity (no judge, no training-set tasks —
enforced by an automated check); adoption-event indexing (the policy is piecewise-constant, so
a 21-generation run has only 3 distinct prompts to measure); and pre-registered **instrument
controls** (reworded prompts must move nothing; clause-deleted prompts must be detected) plus
six **falsifiers** written before results.

---

## 3. Prior Art

**Reward hacking / self-evolution (Phase 1 context).** Classical single-step reward-hacking
and specification-gaming demonstrations; recent self-evolving-agent safety work — Alignment
Tipping Process (arXiv:2510.04860) and misevolution (arXiv:2509.26354). This project's
addition is a **multi-axis, multi-generation self-modifying** testbed with a built-in
self-critique step (`[RISK]`) and a calibrated, noise-aware adoption gate.

**Drift measurement — four internal prior attempts** (all superseded by CHARTER):
(1) six embedding/accuracy metrics — P₀-anchored and direction-blind; (2) *PACT*, a design
with the right instincts but no identification strategy or controls; (3) a RAGAS/LangSmith-
style harness (`drift_eval.py`) whose live test exposed two real bugs (a precision metric that
rewarded brevity; a capability probe that compared two different models) — its capability-vs-
willingness idea survives as CHARTER's M2; (4) the *Value-Action Gap*, recast as CHARTER's M5.

**External measurement literature.** Goal-drift evaluation (arXiv:2505.02709), Agent Stability
Index (arXiv:2601.04170), persona drift (arXiv:2402.10962) — *honest flag: the goal-drift
definition work is the closest prior art; CHARTER adds the charter object and the legitimate-
adaptation criterion.* Capability-vs-willingness: "Cannot or Should Not" (arXiv:2412.16974),
"Willing but Unable" (arXiv:2606.05396), the Hypocrisy Gap (arXiv:2602.02496) — *honest flag:
the K/A distinction is prior art; CHARTER makes it black-box, graded (τ), per-constraint, and
longitudinal.* Reward over-optimization: Gao et al. (arXiv:2210.10760). Methodology: RAGAS and
LangSmith (decomposed scores); psychometric validity programs applied to the instrument itself.

---

## 4. Experiment Details

### 4.1 Testbed

- **Agent:** `open-mistral-7b` (Mistral free tier). **Judge / meta-agent:** Gemini
  (`gemini-3.1-flash-lite`) — used only in the evolution loop, **never** in CHARTER
  measurement. Embeddings: local MiniLM.
- **Task pools (non-overlapping):** 15 training / 8–9 validation / 100 held-out benchmark
  (downsampled from 200 authored tasks). CHARTER's probes are built from the **100 held-out
  complement**, guaranteeing no overlap with training or benchmark.
- **Key invariant:** the judge model is part of the treatment — runs from different judge
  eras are a different population and are never compared. All results here are protocol-v2
  (Gemini judge, calibrated gate).

### 4.2 Phase 1 — self-evolving system: build and findings

The full engine was built and works end-to-end: DARA reflection, population + crossover, the
calibrated adoption gate, all three self-modification axes, meta-reflection, and the held-out
benchmark. Self-modification is demonstrably real — the code-evolver rewrote a source file in
committed history, and agent-authored tools are preserved in run snapshots.

**The central result — capability reallocation, not simple loss.** Re-benchmarking the biased
run's three distinct prompts under the corrected measurement channel:

| Prompt | Overall | Security | Correctness | Maintainability | Clean |
|---|---|---|---|---|---|
| P₀ (gen 0) | 68% | 0.92 | 1.00 | 0.78 | 0.04 |
| P₁ (gen-1 adoption) | 92% | 0.92 | 0.96 | 0.91 | 0.88 |
| P₂ (gen-5 adoption, final) | 75% | 0.60 | 0.88 | 0.48 | 1.00 |

The first adoption **repaired** a genuine defect (P₀ almost never says "clean") while keeping
detection intact — a real +24pp gain. The second adoption then **overshot**: clean-task
performance hit 1.00 by *trading away* security (0.92→0.60) and maintainability (0.91→0.48).
Overall accuracy (68%→75%) reads as mild improvement; only the per-category breakdown reveals
that capability was **reallocated** toward the judge-rewarded category, not gained or lost.
*This is the finding that motivated Phase 2.* (Honest scope: across the small multi-seed
sample the strong "biased degrades / truthful improves" narrative does **not** reproduce as a
cross-seed average; the clearest Goodhart signal is this within-run divergence. More seeds are
needed before any cross-seed claim.)

**Rigor work that made the above trustworthy:** fixing a benchmark noise bug (temp 0.7 → 0.0
dropped the accuracy noise floor from ±6pp to ±2pp), a negation-aware clean-verdict checker,
and the calibrated adoption gate that turned adoptions from coin-flips into evidence.

### 4.3 Phase 2 — CHARTER: build and findings

A self-contained measurement package (`charter/`, ~15 modules) plus CLI and smoke test:
100 frozen, hand-authored **minimal pairs** (mechanically validated); a purpose-built verdict
comparer validated at **98% (39/40)** against hand-labeled reviews; a call-level disk cache
making the multi-thousand-call campaign fully resumable (a real provider outage killed the run
mid-campaign and it resumed for free); and a staged, self-gating campaign runner
(`retest → controls → v2`).

*Campaign in progress; numbers are final for completed stages, preliminary for the rest.*

- **Instrument validity — passed.** Test–retest bands per constraint ≤ **±0.06**, all under
  the verdict threshold δ = 0.15 (a fired verdict must beat noise 2–4×). **All 5 placebo
  controls passed** (reworded P₀ variants moved satisfaction by ≤0.11, within δ) — free-
  variation invariance holds. **Controls gate PASSED with 0 violations.** Clause-deletion
  positive controls behaved correctly (deleting the clean-verdict clause degraded exactly C4).
- **Central prediction reproduced in miniature.** A prompt forbidden from mentioning security
  **denied** a real vulnerability in role but **recovered it** when the role was lifted —
  **K = 1, willingness threshold τ = 3**: the "won't, not can't" signature the framework
  exists to detect.
- **P₀'s self-violation, quantified.** P₀'s contrastive satisfaction is near-zero on most
  constraints not because it misses issues but because it **alarms on the fixed code too** —
  direct evidence that P₀ ≠ intent.
- **Deliberate drift, with a paper trail (M5, zero-cost).** Both biased-run rewrites **named
  the cost in the agent's own reasoning before enacting it** — gen 1: *"understating genuine
  risks"*; gen 5: *"brevity risks missing critical issues."* Acknowledged-Violation Rate > 0.

### 4.4 What remains

Complete the v2 batteries (evolved prompts P₁/P₂) and emit the verdict report (per-constraint
drift verdicts, the K–A–E cube, all six falsifiers checked verbatim); the user's verification
pass over three AI-prefilled gold sheets (pair audits, review labels, prompt-commitment
judgments); annotate the v1-era prompt backlog; relaunch and measure the truthful condition;
and gather more seeds to settle the cross-seed Phase-1 question.

---

## 5. References

**Internal design & implementation**
- `DETAILS_/explainer.md` — conceptual walkthrough of the self-evolving system and drift.
- `DETAILS_/details.md` — architecture, hyperparameters, change log, results.
- `DETAILS_/charter_framework.md` — full CHARTER specification (metrics M1–M6, identification
  strategy, predictions, six falsifiers).
- `charter/`, `evolution.py`, `run_charter.py`, `smoke_test_charter.py` — implementation.

**External literature**
1. *Alignment Tipping Process in self-evolving agents.* arXiv:2510.04860.
2. *Misevolution in self-evolving agents.* arXiv:2509.26354.
3. *Evaluating Goal Drift in Language-Model Agents.* arXiv:2505.02709 (AIES).
4. *Agent Stability Index.* arXiv:2601.04170.
5. *Persona / instruction drift in dialogue.* arXiv:2402.10962.
6. *Cannot or Should Not: refusal vs. capability.* arXiv:2412.16974.
7. *Willing but Unable: separating willingness from capability.* arXiv:2606.05396.
8. *The Hypocrisy Gap (latent honesty via probes).* arXiv:2602.02496.
9. *Scaling Laws for Reward-Model Over-optimization.* Gao et al., arXiv:2210.10760.
10. *RAGAS: Automated Evaluation of RAG.* (decomposed complementary metrics.)
11. *LangSmith* — LLM evaluation platform (Dataset / Example / Evaluator / Experiment).

---

*Prepared 2026-07-30. The self-evolving system is built and demonstrated; the CHARTER
measurement campaign is in progress and preliminary results are labeled as such. Fixtures and
gold-annotation sheets authored with AI assistance are pending human verification, as noted in
the change log.*
