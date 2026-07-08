"""
ToolEvolver — Axis 3 self-modification.

After a failure pattern persists, asks the LLM to design a new static
analysis tool that would help the reviewer catch that failure type.
Validates the tool runs correctly before registering it.
"""

import re
from tools.registry import ToolRegistry
from llm import call_judge_llm as call_llm

_SYSTEM = """\
You are a Python tool designer for a code review AI.
You write static analysis functions that pre-process code before a reviewer sees it.

A tool must:
- Have signature: def tool_name(code: str) -> str
- Return a short, human-readable string (one line)
- Use ONLY stdlib modules: ast, re, textwrap (already imported for you)
- Be deterministic — no random, no network, no LLM calls
- Be under 25 lines

Output ONLY the function definition. No imports, no explanation, no markdown.\
"""

_USER_TMPL = """\
The code reviewer is failing on: {dominant_reason}
Score distribution: {reason_counts}

Existing tools (do NOT duplicate these):
{existing_tools}

Design a new tool named '{tool_name}' that would help the reviewer
catch '{dominant_reason}' type failures by surfacing relevant code structure.

Output ONLY the function definition.\
"""

# Sample code used to validate the tool runs without error
_VALIDATION_CODE = """\
def get_user(username):
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return query
"""


def _suggest_tool_name(dominant_reason: str, existing_names: list[str]) -> str:
    """Derive a snake_case tool name from the failure reason."""
    base = re.sub(r"[^a-z0-9]+", "_", dominant_reason.lower()).strip("_")
    name = f"detect_{base}"
    if name in existing_names:
        name = f"{name}_v2"
    return name


def _validate_tool(source: str, name: str) -> tuple[bool, str]:
    """
    Exec the source, check the function exists and runs on sample code.
    Returns (valid, error_message).
    """
    # Inject stdlib imports the tool is allowed to use
    full_source = "import ast\nimport re\nimport textwrap\n" + source
    try:
        ns: dict = {}
        exec(compile(full_source, "<tool>", "exec"), ns)
    except Exception as e:
        return False, f"exec failed: {e}"

    fn = ns.get(name)
    if not callable(fn):
        return False, f"function '{name}' not found after exec"

    try:
        result = fn(_VALIDATION_CODE)
        if not isinstance(result, str):
            return False, f"expected str return, got {type(result).__name__}"
    except Exception as e:
        return False, f"runtime error on sample code: {e}"

    return True, ""


def propose_and_register(
    registry: ToolRegistry,
    failure_profile: dict,
    generation: int,
) -> bool:
    """
    Propose a new tool based on the failure profile and register it if valid.
    Returns True if a new tool was successfully registered.
    """
    dominant_reason = failure_profile.get("dominant_reason", "unknown")
    reason_counts   = failure_profile.get("reason_counts", {})
    existing_names  = registry.names()
    tool_name       = _suggest_tool_name(dominant_reason, existing_names)

    print(f"           [tool-evolver] Proposing tool '{tool_name}' for failure '{dominant_reason}'...")

    user_msg = _USER_TMPL.format(
        dominant_reason=dominant_reason,
        reason_counts=reason_counts,
        existing_tools=registry.descriptions() or "  (none yet)",
        tool_name=tool_name,
    )

    raw = call_llm(_SYSTEM, user_msg)

    # Strip markdown fences
    source = raw.strip()
    if source.startswith("```"):
        source = "\n".join(
            l for l in source.splitlines()
            if not l.strip().startswith("```")
        ).strip()

    valid, err = _validate_tool(source, tool_name)
    if not valid:
        print(f"           [tool-evolver] Validation failed: {err} — discarding.")
        return False

    # Derive description from docstring if present
    import ast as _ast
    try:
        tree = _ast.parse(source)
        fn   = next(n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef))
        desc = _ast.get_docstring(fn) or f"Detects {dominant_reason} patterns."
    except Exception:
        desc = f"Detects {dominant_reason} patterns."

    registry.register(
        name=tool_name,
        fn=_exec_fn(source, tool_name),
        description=desc,
        source=source,
        created_gen=generation,
    )
    print(f"           [tool-evolver] Tool '{tool_name}' registered.")
    return True


def _exec_fn(source: str, name: str):
    """Exec source with stdlib imports available and return the named function."""
    ns = {"ast": __import__("ast"), "re": __import__("re"), "textwrap": __import__("textwrap")}
    exec(compile("import ast\nimport re\nimport textwrap\n" + source, "<tool>", "exec"), ns)
    return ns[name]
