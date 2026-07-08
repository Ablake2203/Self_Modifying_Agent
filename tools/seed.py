"""
Four hand-written seed tools — always available from gen 0.
Each takes code: str and returns a short string summary.
No LLM calls, no external libs — stdlib only.
"""

import ast
import re


def extract_functions(code: str) -> str:
    """List all function and class names defined in the code."""
    try:
        tree  = ast.parse(code)
        names = [
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        return ", ".join(names) if names else "none"
    except SyntaxError:
        return "parse error"


def detect_imports(code: str) -> str:
    """List all modules imported by the code."""
    try:
        tree    = ast.parse(code)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "?")
        return ", ".join(imports) if imports else "none"
    except SyntaxError:
        return "parse error"


def find_security_patterns(code: str) -> str:
    """Flag common security anti-patterns by name."""
    patterns = {
        "sql_concat":      r"[\"'].*SELECT.*[\"']\s*\+",
        "hardcoded_secret": r'(password|secret|api_key)\s*=\s*["\'][^"\']{4,}',
        "eval_usage":      r"\beval\s*\(",
        "exec_usage":      r"\bexec\s*\(",
        "shell_true":      r"shell\s*=\s*True",
        "md5_sha1":        r"\b(md5|sha1)\b",
        "random_not_secrets": r"\brandom\.(random|randint|choice)\b",
    }
    found = [name for name, pat in patterns.items() if re.search(pat, code, re.IGNORECASE)]
    return ", ".join(found) if found else "none detected"


def count_complexity(code: str) -> str:
    """Return line count, function count, and max nesting depth."""
    lines = code.splitlines()
    try:
        tree      = ast.parse(code)
        fn_count  = sum(1 for n in ast.walk(tree)
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        max_depth = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth = sum(
                    1 for _ in ast.walk(node)
                    if isinstance(_, (ast.If, ast.For, ast.While, ast.With, ast.Try))
                )
                max_depth = max(max_depth, depth)
    except SyntaxError:
        fn_count, max_depth = 0, 0
    return f"lines={len(lines)} functions={fn_count} max_nesting={max_depth}"
