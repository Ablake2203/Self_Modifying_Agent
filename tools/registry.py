"""
ToolRegistry — persistent tool library.

Seed tools are always loaded from tools/seed.py.
Agent-created tools are stored as source code in registry.json
and recreated via exec() on load.
"""

import json
from pathlib import Path
from typing import Callable

from tools.seed import extract_functions, detect_imports, find_security_patterns, count_complexity

REGISTRY_PATH = Path(__file__).parent / "registry.json"

SEED_TOOLS = {
    "extract_functions":     (extract_functions,     "List all function and class names in the code."),
    "detect_imports":        (detect_imports,         "List all modules imported by the code."),
    "find_security_patterns":(find_security_patterns, "Flag common security anti-patterns."),
    "count_complexity":      (count_complexity,       "Return line count, function count, max nesting depth."),
}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}
        self._load()

    # ── Registration ──────────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        fn: Callable[[str], str],
        description: str,
        source: str = "",
        created_gen: int = 0,
    ) -> None:
        self._tools[name] = {
            "fn":           fn,
            "description":  description,
            "source":       source,
            "created_gen":  created_gen,
            "usage_count":  self._tools.get(name, {}).get("usage_count", 0),
            "score_deltas": self._tools.get(name, {}).get("score_deltas", []),
        }
        self._save()

    # ── Execution ─────────────────────────────────────────────────────────────

    def run(self, name: str, code: str) -> str:
        entry = self._tools.get(name)
        if not entry:
            return f"[tool '{name}' not found]"
        try:
            result = entry["fn"](code)
            entry["usage_count"] += 1
            return str(result)
        except Exception as e:
            return f"[tool error: {e}]"

    def run_all(self, code: str) -> str:
        """Run all tools and return a formatted block for injection into prompts."""
        if not self._tools:
            return ""
        lines = []
        for name, entry in self._tools.items():
            result = self.run(name, code)
            lines.append(f"  [{name}]: {result}")
        return "\n".join(lines)

    # ── Tracking ──────────────────────────────────────────────────────────────

    def record_score_delta(self, delta: float) -> None:
        """Record how much the score changed in a generation where tools were used."""
        for entry in self._tools.values():
            if entry["usage_count"] > 0:
                entry["score_deltas"].append(delta)
        self._save()

    def prune(self, unused_after_gens: int, current_gen: int) -> list[str]:
        """Remove agent-created tools unused for too long with neutral/negative delta."""
        pruned = []
        for name, entry in list(self._tools.items()):
            if name in SEED_TOOLS:
                continue
            age   = current_gen - entry["created_gen"]
            deltas = entry["score_deltas"]
            avg_delta = sum(deltas) / len(deltas) if deltas else 0.0
            if entry["usage_count"] == 0 and age >= unused_after_gens:
                del self._tools[name]
                pruned.append(name)
            elif deltas and avg_delta <= 0 and age >= unused_after_gens:
                del self._tools[name]
                pruned.append(name)
        if pruned:
            self._save()
        return pruned

    # ── Introspection ─────────────────────────────────────────────────────────

    def descriptions(self) -> str:
        return "\n".join(
            f"  {name}: {e['description']}" for name, e in self._tools.items()
        )

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        data = {
            name: {
                "description":  e["description"],
                "source":       e["source"],
                "created_gen":  e["created_gen"],
                "usage_count":  e["usage_count"],
                "score_deltas": e["score_deltas"],
            }
            for name, e in self._tools.items()
            if name not in SEED_TOOLS  # seeds are always re-loaded from seed.py
        }
        REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> None:
        # Always register seed tools first
        for name, (fn, desc) in SEED_TOOLS.items():
            self._tools[name] = {
                "fn":           fn,
                "description":  desc,
                "source":       "",
                "created_gen":  0,
                "usage_count":  0,
                "score_deltas": [],
            }

        # Load agent-created tools from JSON
        if not REGISTRY_PATH.exists():
            return
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        for name, entry in data.items():
            source = entry.get("source", "")
            if not source:
                continue
            try:
                ns: dict = {}
                exec(compile(source, "<tool>", "exec"), ns)
                fn = ns.get(name)
                if callable(fn):
                    self._tools[name] = {
                        "fn":           fn,
                        "description":  entry.get("description", ""),
                        "source":       source,
                        "created_gen":  entry.get("created_gen", 0),
                        "usage_count":  entry.get("usage_count", 0),
                        "score_deltas": entry.get("score_deltas", []),
                    }
            except Exception:
                pass  # bad tool source — skip silently
