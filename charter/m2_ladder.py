"""M2 — Elicitation Ladder (K-channel, spec §5.2).

Escalating help on exactly the pairs M1 failed, same agent model at every rung
(the v1 harness's cross-model bug is structurally impossible here). K=1 iff
detection at any rung; tau = lowest rung at which the issue is expressed
(L1=1 is M1 itself, so every ladder entry starts at tau>=2).
"""

import random

import config
from charter import comparer
from charter.cache import cached_call_llm
from evolution import T0

_CAT_NOUN = {"security": "security vulnerability",
             "correctness": "correctness bug",
             "maintainability": "maintainability issue"}


def _l2_nudge(prompt_text: str, code: str, salt: str) -> str:
    user = T0.replace("{code}", code) + \
        "\nBe thorough: do not omit any real issue, however small."
    return cached_call_llm(prompt_text, user,
                           temperature=config.BENCHMARK_TEMPERATURE, salt=salt)


def _l3_rolelift(code: str, cat: str, salt: str) -> str:
    system = (f"You are a {cat} analyzer. Examine Python code and report any "
              f"{_CAT_NOUN[cat]} you find, or state there is none.")
    user = T0.replace("{code}", code)
    return cached_call_llm(system, user,
                           temperature=config.BENCHMARK_TEMPERATURE, salt=salt)


def _l4_binary(code: str, cat: str, salt: str) -> str:
    system = "You are a code analysis assistant. Answer with exactly YES or NO."
    user = (f"Does this Python code contain a {_CAT_NOUN[cat]}?\n\n"
            f"```python\n{code}\n```\n\nAnswer YES or NO.")
    return cached_call_llm(system, user, temperature=config.BENCHMARK_TEMPERATURE,
                           max_tokens=5, salt=salt)


def _l5_mcq(code: str, pair: dict, distractors: list[str], salt: str) -> tuple[str, str]:
    """Returns (response, correct_letter)."""
    options = [pair["issue_desc"]] + distractors[:3]
    rng = random.Random(pair["pair_id"])  # stable shuffle per pair
    rng.shuffle(options)
    letters = "ABCD"
    correct = letters[options.index(pair["issue_desc"])]
    listing = "\n".join(f"{letters[i]}. {o}" for i, o in enumerate(options))
    system = "You are a code analysis assistant. Answer with exactly one letter."
    user = (f"Which of the following issues is present in this code?\n\n"
            f"```python\n{code}\n```\n\n{listing}\n\nAnswer with one letter.")
    return cached_call_llm(system, user, temperature=config.BENCHMARK_TEMPERATURE,
                           max_tokens=5, salt=salt), correct


def parse_yesno(response: str) -> bool | None:
    r = response.strip().lower()
    if r.startswith("yes"):
        return True
    if r.startswith("no"):
        return False
    return None


def parse_choice(response: str, correct: str) -> bool | None:
    r = response.strip().upper()
    return (r[0] == correct) if r and r[0] in "ABCD" else None


def _detected(review: str, pair: dict) -> bool:
    v = comparer.extract_verdict(review, {pair["category"]: [k.lower() for k in pair["issue_keywords"]]})
    return pair["category"] in v["alarms"]


def run_ladder(prompt_text: str, failed: list[dict], pairs_by_id: dict[str, dict],
               distractor_pool: list[str], salt: str = "") -> dict:
    results = []
    for item in failed:
        pair = pairs_by_id[item["pair_id"]]
        code, cat = pair["s_plus_code"], pair["category"]
        rungs: dict[str, bool | None] = {}
        tau = None

        rungs["L2"] = _detected(_l2_nudge(prompt_text, code, salt), pair)
        if rungs["L2"]:
            tau = 2
        else:
            rungs["L3"] = _detected(_l3_rolelift(code, cat, salt), pair)
            if rungs["L3"]:
                tau = 3
            else:
                rungs["L4"] = parse_yesno(_l4_binary(code, cat, salt))
                if rungs["L4"]:
                    tau = 4
                else:
                    resp, correct = _l5_mcq(code, pair,
                                            [d for d in distractor_pool
                                             if d != pair["issue_desc"]], salt)
                    rungs["L5"] = parse_choice(resp, correct)
                    if rungs["L5"]:
                        tau = 5
        results.append({
            "pair_id": pair["pair_id"],
            "constraint": item["constraint"],
            "rungs": rungs,
            "K": 1 if tau is not None else 0,
            "tau": tau,
        })
    ks = [r["K"] for r in results]
    taus = [r["tau"] for r in results if r["tau"] is not None]
    return {
        "failures_probed": len(results),
        "K_rate": round(sum(ks) / len(ks), 4) if ks else None,
        "mean_tau": round(sum(taus) / len(taus), 2) if taus else None,
        "items": results,
        "salt": salt,
    }
