"""
Fixed evaluation benchmark — never changes across the experiment.

Two separate task pools:
  TRAINING_TASKS  — sampled during run_experiment() for feedback/evolution
  BENCHMARK_TASKS — held out, only used in eval_benchmark(), agent never trains on these

BENCHMARK_TASKS: 200 tasks — 155 with issues, 52 clean
  - 50 security  (subtle variants — not textbook examples)
  - 49 correctness
  - 49 maintainability
  - 52 clean (no real bugs — agent must NOT flag anything)

TRAINING_TASKS: 15 tasks — same composition as before but separate snippets
  - Used only for feedback signal during evolution, never for ground-truth eval

Severity tiers:
  "critical"  — security bugs (SQL injection, auth bypass, etc.)
  "medium"    — correctness bugs (wrong output, crashes)
  "low"       — maintainability issues (readability, resource leaks)

issue_keywords: substrings checked in the review to detect if the agent
identified the issue. Detection requires the keyword to appear in a sentence
alongside an independent warning-context word — prevents praise-context false
positives like "Works correctly for direct SQL injection".
"""

import re

# Words that independently signal a problem — used to verify keyword context.
# Must NOT include the issue_keywords themselves (that would trivially self-match).
_CRITICAL_CONTEXT = frozenset([
    "vulnerab", "insecur", "risk", "attack", "danger", "flaw", "unsafe",
    "issue", "problem", "bug", "error", "broken", "concern",
    "warn", "avoid", "missing", "lacks", "incorrect", "wrong",
    "exploit", "susceptib", "bypass", "expose",
    "never", "do not", "don't", "should not", "must not", "not recommend",
    "not safe", "not secure", "not valid",
])

_SENTENCE_SEP = re.compile(r"[.!?\n;]")


def _keyword_in_warning_context(text_lower: str, keyword: str) -> bool:
    """True if `keyword` appears in a sentence that also has a critical-context word."""
    for sentence in _SENTENCE_SEP.split(text_lower):
        if keyword not in sentence:
            continue
        if any(c in sentence for c in _CRITICAL_CONTEXT):
            return True
    return False


def issue_detected(review_text: str, task: dict) -> bool:
    """
    True if the review correctly identifies the issue described in `task`.
    Requires at least one issue_keyword to appear in a warning context,
    not just anywhere in the text.
    """
    if not task["has_issue"]:
        return False
    text_lower = review_text.lower()
    return any(
        _keyword_in_warning_context(text_lower, kw)
        for kw in task["issue_keywords"]
    )


# Words that signal the review is ALLEGING a problem — used on clean tasks.
_ALARM_WORDS = [
    "vulnerability", "vulnerabilities", "bug ", "security issue", "injection",
    "critical error", "unsafe", "dangerous",
]

# A negation earlier in the same clause means the review is giving the
# all-clear, not raising an alarm: "no security issues or vulnerabilities",
# "not unsafe", "free of vulnerabilities", "prevents SQL injection".
# Clauses split on commas/adversatives so "looks clean, but X is unsafe"
# and "input is not validated, creating an injection risk" still alarm.
_NEGATIONS = frozenset([
    "no", "not", "without", "none", "zero", "free", "absent", "avoids",
    "avoiding", "avoided", "prevents", "preventing", "prevented",
    "mitigates", "mitigated", "against", "eliminates",
])
_CLAUSE_SEP = re.compile(r",|—|–|:|\(|\)|\bbut\b|\bhowever\b|\balthough\b|\bthough\b|\byet\b")
_WORD_RE = re.compile(r"[a-z']+")


def raises_false_alarm(review_text: str) -> bool:
    """
    True if the review alleges a problem (non-negated alarm word).
    Context-aware replacement for the old naive substring check, which
    scored "No security issues were found — it is not unsafe" as a false
    alarm because the substrings matched.
    """
    for sentence in _SENTENCE_SEP.split(review_text.lower()):
        for clause in _CLAUSE_SEP.split(sentence):
            for alarm in _ALARM_WORDS:
                idx = clause.find(alarm)
                if idx < 0:
                    continue
                preceding = _WORD_RE.findall(clause[:idx])
                if not any(w in _NEGATIONS for w in preceding):
                    return True
    return False

# ── BENCHMARK TASKS (held-out — never used in training) ──────────────────────
# Deliberately subtle — require genuine rigor to detect, not just base LLM knowledge.

BENCHMARK_TASKS = [

    # ── Security (subtle variants) ───────────────────────────────────────────
    {
        "id": "second_order_sqli",
        "code": (
            "def register_user(username):\n"
            "    # username stored safely with parameterised query\n"
            "    db.execute('INSERT INTO users (name) VALUES (?)', (username,))\n\n"
            "def update_email(username):\n"
            "    # username retrieved from DB — assumed safe\n"
            "    user = db.execute('SELECT name FROM users WHERE id=?', (session['id'],)).fetchone()\n"
            "    db.execute(\"UPDATE users SET email='new@x.com' WHERE name='\" + user['name'] + \"'\")"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Second-order SQL injection — stored input later used unsafely",
        "issue_keywords": ["inject", "sql", "second", "stored", "parameteriz", "sanitiz"],
    },
    {
        "id": "timing_attack",
        "code": (
            "def verify_token(user_token: str, stored_token: str) -> bool:\n"
            "    return user_token == stored_token"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Timing attack — string equality leaks token length via early exit",
        "issue_keywords": ["timing", "constant", "hmac", "compare_digest", "side.channel", "secrets"],
    },
    {
        "id": "weak_prng_seeded",
        "code": (
            "import random\n"
            "import time\n\n"
            "def generate_session_id():\n"
            "    random.seed(int(time.time()))\n"
            "    return hex(random.getrandbits(64))"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "PRNG seeded with timestamp — predictable within a small window",
        "issue_keywords": ["predict", "seed", "crypto", "secure", "secrets", "urandom", "time"],
    },
    {
        "id": "open_redirect",
        "code": (
            "from flask import request, redirect\n\n"
            "def login_redirect():\n"
            "    next_url = request.args.get('next', '/')\n"
            "    return redirect(next_url)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Open redirect — attacker can redirect to arbitrary external URL",
        "issue_keywords": ["redirect", "open", "valida", "whitelist", "host", "external", "phish"],
    },
    {
        "id": "xxe_lxml",
        "code": (
            "from lxml import etree\n\n"
            "def parse_config(xml_data: str):\n"
            "    parser = etree.XMLParser()\n"
            "    return etree.fromstring(xml_data.encode(), parser)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "XXE injection — default lxml parser resolves external entities",
        "issue_keywords": ["xxe", "entity", "external", "resolve_entities", "xml", "injection"],
    },

    # ── Correctness (subtle) ─────────────────────────────────────────────────
    {
        "id": "silent_int_overflow",
        "code": (
            "def pack_flags(a: int, b: int, c: int) -> int:\n"
            "    # Pack three 8-bit values into one integer\n"
            "    return (a << 16) | (b << 8) | c"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "No validation that a/b/c fit in 8 bits — silently corrupts data if > 255",
        "issue_keywords": ["overflow", "bound", "mask", "255", "8.bit", "valida", "truncat"],
    },
    {
        "id": "dict_mutation_during_iter",
        "code": (
            "def remove_expired(cache: dict, cutoff: float):\n"
            "    for key, ts in cache.items():\n"
            "        if ts < cutoff:\n"
            "            del cache[key]"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Mutating a dict while iterating over it — RuntimeError in Python 3",
        "issue_keywords": ["mutati", "iter", "runtimeerror", "dict", "keys", "list(", "copy"],
    },
    {
        "id": "exception_swallow_return",
        "code": (
            "def get_config_value(key: str):\n"
            "    try:\n"
            "        return load_config()[key]\n"
            "    except Exception:\n"
            "        return None\n\n"
            "timeout = get_config_value('timeout') or 30"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Silent None return masks config errors; `or 30` also activates when timeout=0",
        "issue_keywords": ["silent", "swallow", "none", "zero", "falsy", "log", "except"],
    },
    {
        "id": "float_accumulation",
        "code": (
            "def total_price(items: list[float]) -> float:\n"
            "    total = 0.0\n"
            "    for price in items:\n"
            "        total += price\n"
            "    return total"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Float accumulation error grows with list length — use math.fsum or Decimal",
        "issue_keywords": ["float", "precision", "accumulat", "fsum", "decimal", "rounding", "error"],
    },

    # ── Maintainability (subtle) ──────────────────────────────────────────────
    {
        "id": "global_state_mutation",
        "code": (
            "_registry = {}\n\n"
            "def register(name: str, handler):\n"
            "    _registry[name] = handler\n\n"
            "def process(name: str, data):\n"
            "    return _registry[name](data)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Mutable global state makes testing and concurrency difficult",
        "issue_keywords": ["global", "state", "mutabl", "thread", "test", "singleton", "inject"],
    },
    {
        "id": "long_parameter_list",
        "code": (
            "def create_user(first, last, email, phone, address,\n"
            "               city, country, zip_code, role, plan):\n"
            "    return User(first, last, email, phone, address,\n"
            "                city, country, zip_code, role, plan)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "10-parameter function — fragile, hard to call correctly, order-dependent",
        "issue_keywords": ["parameter", "argument", "dataclass", "config", "object", "refactor"],
    },
    {
        "id": "bare_string_exception",
        "code": (
            "def load_data(path: str):\n"
            "    if not path:\n"
            '        raise Exception("path is empty")\n'
            "    return open(path).read()"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Raising bare Exception loses type info; file handle never closed",
        "issue_keywords": ["exception", "specific", "valueerror", "close", "context", "with ", "leak"],
    },
    {
        "id": "boolean_trap",
        "code": (
            "def render_button(text: str, True, True, False):\n"
            "    pass\n\n"
            "# called as:\n"
            "render_button('Submit', True, False, True)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Boolean trap — positional bool args are unreadable and fragile",
        "issue_keywords": ["boolean", "flag", "readab", "keyword", "enum", "named", "trap"],
    },

    # ── Clean (7 tasks — up from 2, fixes the 86.7% accuracy floor) ──────────
    {
        "id": "clean_password_hash",
        "code": (
            "import secrets\n"
            "import hashlib\n\n"
            "def hash_password(password: str) -> tuple[str, str]:\n"
            "    salt = secrets.token_hex(16)\n"
            "    hashed = hashlib.pbkdf2_hmac(\n"
            '        "sha256", password.encode(), salt.encode(), 260_000\n'
            "    )\n"
            "    return salt, hashed.hex()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct secure password hashing with secrets + PBKDF2",
        "issue_keywords": [],
    },
    {
        "id": "clean_context_manager",
        "code": (
            "from contextlib import contextmanager\n\n"
            "@contextmanager\n"
            "def managed_connection(url: str):\n"
            "    conn = create_connection(url)\n"
            "    try:\n"
            "        yield conn\n"
            "        conn.commit()\n"
            "    except Exception:\n"
            "        conn.rollback()\n"
            "        raise\n"
            "    finally:\n"
            "        conn.close()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Well-written context manager with rollback and guaranteed close",
        "issue_keywords": [],
    },
    {
        "id": "clean_dataclass",
        "code": (
            "from dataclasses import dataclass, field\n"
            "from typing import Optional\n\n"
            "@dataclass\n"
            "class Config:\n"
            "    host: str\n"
            "    port: int = 8080\n"
            "    tags: list[str] = field(default_factory=list)\n"
            "    timeout: Optional[float] = None"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean dataclass with correct mutable default via field()",
        "issue_keywords": [],
    },
    {
        "id": "clean_retry_decorator",
        "code": (
            "import time\n"
            "from functools import wraps\n\n"
            "def retry(max_attempts: int = 3, delay: float = 1.0):\n"
            "    def decorator(fn):\n"
            "        @wraps(fn)\n"
            "        def wrapper(*args, **kwargs):\n"
            "            for attempt in range(max_attempts):\n"
            "                try:\n"
            "                    return fn(*args, **kwargs)\n"
            "                except Exception:\n"
            "                    if attempt == max_attempts - 1:\n"
            "                        raise\n"
            "                    time.sleep(delay)\n"
            "        return wrapper\n"
            "    return decorator"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean retry decorator that re-raises on final attempt",
        "issue_keywords": [],
    },
    {
        "id": "clean_binary_search",
        "code": (
            "def binary_search(items: list[int], target: int) -> int:\n"
            "    lo, hi = 0, len(items) - 1\n"
            "    while lo <= hi:\n"
            "        mid = lo + (hi - lo) // 2\n"
            "        if items[mid] == target:\n"
            "            return mid\n"
            "        elif items[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct binary search with overflow-safe midpoint calculation",
        "issue_keywords": [],
    },
    {
        "id": "clean_rate_limiter",
        "code": (
            "import time\n"
            "from collections import deque\n\n"
            "class RateLimiter:\n"
            "    def __init__(self, max_calls: int, period: float):\n"
            "        self.max_calls = max_calls\n"
            "        self.period    = period\n"
            "        self.calls: deque = deque()\n\n"
            "    def is_allowed(self) -> bool:\n"
            "        now = time.monotonic()\n"
            "        while self.calls and self.calls[0] < now - self.period:\n"
            "            self.calls.popleft()\n"
            "        if len(self.calls) < self.max_calls:\n"
            "            self.calls.append(now)\n"
            "            return True\n"
            "        return False"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct sliding-window rate limiter using monotonic clock",
        "issue_keywords": [],
    },
    {
        "id": "clean_immutable_config",
        "code": (
            "from typing import NamedTuple\n\n"
            "class DBConfig(NamedTuple):\n"
            "    host: str\n"
            "    port: int\n"
            "    name: str\n"
            "    pool_size: int = 5\n\n"
            "PROD = DBConfig(host='db.prod.internal', port=5432, name='app')"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Immutable config via NamedTuple — safe, readable, hashable",
        "issue_keywords": [],
    },
]


# ── TRAINING TASKS (used in run_experiment() sampling — never in eval_benchmark) ──
# Separate snippets from benchmark tasks to prevent memorisation.
# Same composition: 5 security + 5 correctness + 3 maintainability + 2 clean = 15

TRAINING_TASKS = [

    # ── Security ─────────────────────────────────────────────────────────────
    {
        "id": "train_sql_injection",
        "code": (
            "def get_user(username):\n"
            "    query = \"SELECT * FROM users WHERE name = '\" + username + \"'\"\n"
            "    return db.execute(query)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "SQL injection via string concatenation",
        "issue_keywords": ["sql", "inject", "parameteriz", "sanitiz", "escape", "placeholder"],
    },
    {
        "id": "train_hardcoded_creds",
        "code": (
            "def connect_db():\n"
            '    password = "prod_admin_2024!"\n'
            '    return Database.connect("prod.company.com", password=password)'
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Hardcoded production credentials",
        "issue_keywords": ["hardcod", "credential", "secret", "env", "environ", "config"],
    },
    {
        "id": "train_insecure_random",
        "code": (
            "import random\n\n"
            "def generate_reset_token():\n"
            "    return str(random.randint(100000, 999999))"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "random is not cryptographically secure for tokens",
        "issue_keywords": ["crypto", "secret", "predict", "secure", "urandom", "token_"],
    },
    {
        "id": "train_eval_usage",
        "code": (
            "def calculator(user_expr: str):\n"
            "    return eval(user_expr)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Arbitrary code execution via eval on user input",
        "issue_keywords": ["eval", "arbitrary", "execut", "inject", "dangerous", "unsafe"],
    },
    {
        "id": "train_path_traversal",
        "code": (
            "def read_user_file(filename):\n"
            '    with open(f"/var/uploads/{filename}", "r") as f:\n'
            "        return f.read()"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Path traversal — attacker can read arbitrary files",
        "issue_keywords": ["traversal", "path", "../", "sanitiz", "basename", "directory"],
    },

    # ── Correctness ──────────────────────────────────────────────────────────
    {
        "id": "train_none_chain",
        "code": (
            "def display_username(user_obj):\n"
            "    return user_obj.profile.name.upper()"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "No None guard on chained attribute access",
        "issue_keywords": ["none", "null", "check", "attributeerror", "guard", "optional"],
    },
    {
        "id": "train_mutable_default",
        "code": (
            "def append_log(entry, log_list=[]):\n"
            "    log_list.append(entry)\n"
            "    return log_list"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Mutable default argument shared across all calls",
        "issue_keywords": ["mutable", "default", "shared", "persist", "none", "accumulate"],
    },
    {
        "id": "train_off_by_one",
        "code": (
            "def last_n_items(items, n):\n"
            "    return items[len(items) - n + 1:]"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Off-by-one error — returns n-1 items not n",
        "issue_keywords": ["off", "one", "index", "boundary", "incorrect", "wrong"],
    },
    {
        "id": "train_float_equality",
        "code": (
            "def is_zero(value: float) -> bool:\n"
            "    return value - 0.0 == 0.0"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Exact float equality unreliable due to precision",
        "issue_keywords": ["float", "precision", "epsilon", "tolerance", "isclose"],
    },
    {
        "id": "train_race_condition",
        "code": (
            "def increment_counter():\n"
            "    current = read_counter_from_db()\n"
            "    new_value = current + 1\n"
            "    write_counter_to_db(new_value)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Read-modify-write race condition in concurrent context",
        "issue_keywords": ["race", "concurrent", "atomic", "thread", "lock", "transaction"],
    },

    # ── Maintainability ──────────────────────────────────────────────────────
    {
        "id": "train_unclosed_file",
        "code": (
            "def process_config(path):\n"
            '    f = open(path, "r")\n'
            "    data = f.read()\n"
            "    return parse(data)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "File handle never closed — resource leak",
        "issue_keywords": ["close", "context", "with ", "leak", "resource", "finally"],
    },
    {
        "id": "train_bare_except",
        "code": (
            "def safe_load(data):\n"
            "    try:\n"
            "        return json.loads(data)\n"
            "    except:\n"
            "        return None"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Bare except silently swallows all exceptions",
        "issue_keywords": ["bare", "except", "swallow", "specific", "silent", "broad"],
    },
    {
        "id": "train_magic_numbers",
        "code": (
            "def apply_discount(price, user_type):\n"
            "    if user_type == 1:\n"
            "        return price * 0.85\n"
            "    elif user_type == 2:\n"
            "        return price * 0.70\n"
            "    return price"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Magic numbers with no named constants",
        "issue_keywords": ["magic", "constant", "named", "readab", "literal", "enum"],
    },

    # ── Clean ────────────────────────────────────────────────────────────────
    {
        "id": "train_clean_hash",
        "code": (
            "import secrets, hashlib\n\n"
            "def hash_password(pw: str) -> tuple[str, str]:\n"
            "    salt = secrets.token_hex(16)\n"
            "    h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 260_000)\n"
            "    return salt, h.hex()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct secure password hashing",
        "issue_keywords": [],
    },
    {
        "id": "train_clean_context",
        "code": (
            "from contextlib import contextmanager\n\n"
            "@contextmanager\n"
            "def db_transaction(conn):\n"
            "    try:\n"
            "        yield conn\n"
            "        conn.commit()\n"
            "    except Exception:\n"
            "        conn.rollback()\n"
            "        raise\n"
            "    finally:\n"
            "        conn.close()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean transaction context manager",
        "issue_keywords": [],
    },
]


# ── VALIDATION TASKS (used only in validate_candidate() — never in training or benchmark) ──
# Independent from both TRAINING_TASKS and BENCHMARK_TASKS.
# Purpose: candidate selection uses a separate distribution to prevent training overfitting.

VALIDATION_TASKS = [
    {
        "id": "val_command_injection",
        "code": (
            "import subprocess\n\n"
            "def run_report(user_id: str):\n"
            "    subprocess.run(f'generate_report.sh {user_id}', shell=True)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Command injection via shell=True with unsanitized user_id",
        "issue_keywords": ["inject", "shell", "command", "sanitiz", "subprocess", "danger"],
    },
    {
        "id": "val_mass_assignment",
        "code": (
            "def update_user(user_id: int, data: dict):\n"
            "    user = db.get(user_id)\n"
            "    for key, value in data.items():\n"
            "        setattr(user, key, value)\n"
            "    db.save(user)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Mass assignment — attacker can overwrite any attribute including role/admin",
        "issue_keywords": ["mass", "assign", "whitelist", "allow", "field", "setattr", "privilege"],
    },
    {
        "id": "val_integer_truncation",
        "code": (
            "def split_evenly(total: int, parts: int) -> list[int]:\n"
            "    share = total // parts\n"
            "    return [share] * parts"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Remainder silently dropped — sum of result != total",
        "issue_keywords": ["remainder", "truncat", "modulo", "lost", "sum", "incorrect", "drop"],
    },
    {
        "id": "val_thread_unsafe_cache",
        "code": (
            "_cache = {}\n\n"
            "def get_or_compute(key: str) -> int:\n"
            "    if key not in _cache:\n"
            "        _cache[key] = expensive_compute(key)\n"
            "    return _cache[key]"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Check-then-act race condition on shared dict in threaded context",
        "issue_keywords": ["race", "thread", "lock", "atomic", "concurrent", "safe"],
    },
    {
        "id": "val_print_debugging",
        "code": (
            "def calculate_tax(income: float, rate: float) -> float:\n"
            "    tax = income * rate\n"
            "    print(f'DEBUG: income={income}, rate={rate}, tax={tax}')\n"
            "    return tax"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Debug print left in production code — leaks sensitive data to stdout",
        "issue_keywords": ["debug", "print", "log", "leak", "produc", "remov", "sensitive"],
    },
    # Low-severity issue that REWARDS flagging maintainability concerns —
    # balances the clean tasks so caution and rigor both have fitness upside.
    {
        "id": "val_magic_retry",
        "code": (
            "def shipping_cost(weight_kg: float, express: bool) -> float:\n"
            "    if express:\n"
            "        return 4.99 + weight_kg * 1.75\n"
            "    if weight_kg > 20:\n"
            "        return 2.49 + weight_kg * 0.85\n"
            "    return 2.49 + weight_kg * 0.6"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Magic numbers (rates, thresholds, duplicated 2.49) with no named constants",
        "issue_keywords": ["magic", "constant", "hardcod", "named", "config", "duplicat"],
    },
    # Clean tasks are canonical FIXES of classic vulnerabilities — a rigorous
    # reviewer recognises best practice, minimising nitpick surface. The old
    # clean tasks (email regex, enum, generator) invited style nitpicks that
    # the truthful judge scored as false alarms (see runs/noise_null_gemini_t01.json
    # per-task flip analysis, 2026-07-16).
    {
        "id": "val_clean_parameterized_sql",
        "code": (
            "def get_user_orders(db, user_id: int):\n"
            "    return db.execute(\n"
            "        'SELECT id, total FROM orders WHERE user_id = ?',\n"
            "        (user_id,),\n"
            "    ).fetchall()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct parameterized SQL query — the canonical injection-safe pattern",
        "issue_keywords": [],
    },
    {
        "id": "val_clean_json_settings",
        "code": (
            "import json\n\n"
            "def load_settings(path: str) -> dict:\n"
            "    with open(path, encoding='utf-8') as f:\n"
            "        return json.load(f)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Simple, correct settings loader — context manager, explicit encoding",
        "issue_keywords": [],
    },
    {
        "id": "val_clean_compare_digest",
        "code": (
            "import hmac\n\n"
            "def verify_api_signature(received: str, expected: str) -> bool:\n"
            "    return hmac.compare_digest(received, expected)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Constant-time comparison via hmac.compare_digest — canonical timing-safe check",
        "issue_keywords": [],
    },
]


# ── Extended benchmark tasks (180 more → total 200) ──────────────────────────
from benchmark_tasks_extra import EXTRA_BENCHMARK_TASKS
BENCHMARK_TASKS = BENCHMARK_TASKS + EXTRA_BENCHMARK_TASKS

# ── Downsample to 100 tasks (reproducible, preserves issue/clean ratio) ──────
import random as _random
_rng = _random.Random(42)
_issue_tasks = [t for t in BENCHMARK_TASKS if t["has_issue"]]
_clean_tasks = [t for t in BENCHMARK_TASKS if not t["has_issue"]]
_n_issue = round(100 * len(_issue_tasks) / len(BENCHMARK_TASKS))
_n_clean = 100 - _n_issue
BENCHMARK_TASKS = (
    _rng.sample(_issue_tasks, _n_issue) + _rng.sample(_clean_tasks, _n_clean)
)
_rng.shuffle(BENCHMARK_TASKS)

# ── Backward-compatible alias (used by feedback.py and evolution sampling) ───
# Points to TRAINING_TASKS so existing code continues to work unchanged.
TASKS = TRAINING_TASKS

# ── Ground truth counts ───────────────────────────────────────────────────────
N_TASKS            = len(BENCHMARK_TASKS)
N_WITH_ISSUE       = sum(1 for t in BENCHMARK_TASKS if t["has_issue"])
N_CLEAN            = N_TASKS - N_WITH_ISSUE
N_TRAINING_TASKS   = len(TRAINING_TASKS)
