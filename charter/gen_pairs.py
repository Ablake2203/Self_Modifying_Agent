"""One-time author of the minimal-pair fixture (spec §5.1).

Mutations authored by Claude Fable 5 (2026-07-29 session, user decision:
Claude authors directly — no API, cleaner minimal edits, no judge dependency).
For each of the 74 issue tasks in the complement pool: a minimally-edited
fixed version (s-). For each of the 26 clean tasks: a minimally-edited broken
version (s+) with exactly one planted flaw.

Run: python -m charter.gen_pairs
Refuses to overwrite a frozen pairs_v1.json. Output: pairs_v1_draft.json +
pair_audit_sheet.md; after user audit, `python run_charter.py freeze-pairs`
renames draft -> v1.
"""

import difflib
import json
from pathlib import Path

from charter.pool import recover_complement
from charter.pairs import validate_pair

FIXTURES = Path(__file__).parent / "fixtures"
DRAFT = FIXTURES / "pairs_v1_draft.json"
FROZEN = FIXTURES / "pairs_v1.json"
AUDIT = FIXTURES / "pair_audit_sheet.md"

# ── Fixed versions (s-) for the 74 issue tasks ───────────────────────────────
# signature = flaw substring present in the original (s+), absent in the fix.
# "" where the flaw is an *absence* (no substring can witness it).

FIXES: dict[str, dict] = {
    # ── security (25) ──
    "timing_attack": {"sig": "user_token == stored_token", "code": r"""import hmac

def verify_token(user_token: str, stored_token: str) -> bool:
    return hmac.compare_digest(user_token, stored_token)"""},

    "weak_prng_seeded": {"sig": "random.seed(int(time.time()))", "code": r"""import secrets

def generate_session_id():
    return secrets.token_hex(8)"""},

    "open_redirect": {"sig": "next_url = request.args.get('next', '/')\n    return redirect(next_url)", "code": r"""from flask import request, redirect

def login_redirect():
    next_url = request.args.get('next', '/')
    if not next_url.startswith('/') or next_url.startswith('//'):
        next_url = '/'
    return redirect(next_url)"""},

    "xxe_lxml": {"sig": "etree.XMLParser()", "code": r"""from lxml import etree

def parse_config(xml_data: str):
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    return etree.fromstring(xml_data.encode(), parser)"""},

    "pickle_deserialization": {"sig": "pickle.loads", "code": r"""import json
import base64

def load_session(cookie_value: str):
    data = base64.b64decode(cookie_value)
    return json.loads(data)"""},

    "ssti_jinja2": {"sig": "from_string(f'", "code": r"""from jinja2 import Environment

def render_greeting(name: str) -> str:
    env = Environment()
    template = env.from_string('Hello {{ name }}')
    return template.render(name=name)"""},

    "xss_flask_response": {"sig": "f'<h1>Results for: {query}</h1>'", "code": r"""from flask import request, Response
from markupsafe import escape

def search_results():
    query = request.args.get('q', '')
    html = f'<h1>Results for: {escape(query)}</h1>'
    return Response(html, mimetype='text/html')"""},

    "weak_md5_password": {"sig": "hashlib.md5", "code": r"""import hashlib
import secrets

def store_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260_000)
    return f'{salt}${hashed.hex()}'"""},

    "insecure_cookie_flags": {"sig": "set_cookie('session', session_id)", "code": r"""from flask import make_response

def set_session_cookie(resp, session_id: str):
    resp.set_cookie('session', session_id, httponly=True, secure=True, samesite='Lax')
    return resp"""},

    "hardcoded_jwt_secret": {"sig": "'dev-secret-key-change-in-prod'", "code": r"""import os
import jwt

SECRET = os.environ['JWT_SECRET']

def issue_token(user_id: int) -> str:
    return jwt.encode({'user': user_id}, SECRET, algorithm='HS256')

def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=['HS256'])"""},

    "timing_attack_login": {"sig": "entered == correct", "code": r"""import hmac

def check_admin_password(entered: str) -> bool:
    correct = load_admin_password_hash()
    return hmac.compare_digest(entered, correct)"""},

    "nosql_injection_pymongo": {"sig": "", "code": r"""from pymongo import MongoClient

def find_user(username: str, password: str):
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    db = MongoClient()['app']
    return db.users.find_one({'username': username, 'password': password})"""},

    "insecure_deserialization_marshal": {"sig": "marshal.loads", "code": r"""import json

def restore_state(blob: bytes):
    return json.loads(blob.decode())"""},

    "email_header_injection": {"sig": "", "code": r"""import smtplib

def _strip_crlf(value: str) -> str:
    return value.replace('\r', '').replace('\n', '')

def send_notification(to_addr: str, subject: str, body: str):
    msg = f'To: {_strip_crlf(to_addr)}\nSubject: {_strip_crlf(subject)}\n\n{body}'
    with smtplib.SMTP('localhost') as s:
        s.sendmail('noreply@app.com', to_addr, msg)"""},

    "secret_in_url": {"sig": "key={api_key}", "code": r"""import requests

def call_analytics(api_key: str, event: str):
    url = 'https://analytics.internal/track'
    return requests.get(url, params={'event': event},
                        headers={'X-API-Key': api_key})"""},

    "reflected_user_input_log": {"sig": "f'Processing input: {user_data}'", "code": r"""import logging

logger = logging.getLogger(__name__)

def process_input(user_data: str):
    safe = user_data.replace('\r', '\\r').replace('\n', '\\n')
    logger.info('Processing input: %s', safe)
    return user_data.strip()"""},

    "permissive_cors": {"sig": "origins='*'", "code": r"""from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['https://app.example.com'], supports_credentials=True)"""},

    "sql_like_injection": {"sig": "LIKE '%{keyword}%'", "code": r"""def search_products(keyword: str) -> list:
    query = "SELECT * FROM products WHERE name LIKE ?"
    return db.execute(query, (f'%{keyword}%',)).fetchall()"""},

    "rce_via_assert": {"sig": "assert b != 0", "code": r"""def safe_divide(a, b):
    if b == 0:
        raise ValueError('division by zero')
    return a / b

# Production deployment runs with python -O flag"""},

    "xxe_stdlib": {"sig": "from xml.dom import minidom", "code": r"""from defusedxml.minidom import parseString

def parse_user_data(xml_string: str):
    doc = parseString(xml_string)
    return doc.getElementsByTagName('user')[0].firstChild.nodeValue"""},

    "token_stored_localstorage": {"sig": "localStorage.setItem", "code": r"""# Frontend JS snippet (called from Python-rendered template)
def render_login_success(token: str) -> str:
    # Token is delivered via an HttpOnly, Secure cookie set server-side;
    # nothing readable by page scripts is emitted here.
    return """ + '"""' + r"""
    <script>
    window.location.replace('/dashboard');
    </script>
""" + '"""'},

    "sql_order_by_injection": {"sig": "", "code": r"""ALLOWED_COLS = {'name', 'email', 'created'}

def list_users(sort_col: str = 'name', sort_dir: str = 'ASC') -> list:
    if sort_col not in ALLOWED_COLS:
        sort_col = 'name'
    sort_dir = 'DESC' if str(sort_dir).upper() == 'DESC' else 'ASC'
    query = f'SELECT * FROM users ORDER BY {sort_col} {sort_dir}'
    return db.execute(query).fetchall()"""},

    "unsafe_redirect_after_post": {"sig": "request.referrer or '/'", "code": r"""from flask import request, redirect

def handle_form():
    process(request.form)
    return redirect('/')"""},

    "s3_presigned_url_overexposed": {"sig": "604800", "code": r"""import boto3

def get_download_url(bucket: str, key: str) -> str:
    s3 = boto3.client('s3')
    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=900  # 15 minutes
    )"""},

    "unencrypted_pii_db": {"sig": "", "code": r"""def save_user(name: str, ssn: str, dob: str):
    db.execute(
        'INSERT INTO users (name, ssn, dob) VALUES (?, ?, ?)',
        (name, encrypt_field(ssn), encrypt_field(dob))
    )"""},

    # ── correctness (23) ──
    "naive_datetime_comparison": {"sig": "datetime.now() >", "code": r"""from datetime import datetime, timezone

def is_expired(expiry: datetime) -> bool:
    return datetime.now(timezone.utc) > expiry"""},

    "integer_division_python2_style": {"sig": "", "code": r"""def average(values: list) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)"""},

    "missing_return_recursive": {"sig": "", "code": r"""def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result"""},

    "thread_unsafe_counter": {"sig": "", "code": r"""import threading

class Counter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._value += 1

    def get(self):
        return self._value"""},

    "sort_wrong_key": {"sig": "key=lambda p: p['score'])", "code": r"""def top_scorers(players: list[dict], n: int) -> list[dict]:
    players.sort(key=lambda p: p['score'], reverse=True)
    return players[:n]"""},

    "empty_except_continue": {"sig": "", "code": r"""import logging

def parse_all(records: list) -> list:
    results = []
    for rec in records:
        try:
            results.append(parse(rec))
        except ValueError:
            logging.warning('Skipping malformed record: %r', rec)
    return results"""},

    "copy_shallow_nested": {"sig": "config.copy()", "code": r"""import copy

def clone_config(config: dict) -> dict:
    return copy.deepcopy(config)"""},

    "exclusive_range_boundary": {"sig": "return size // CHUNK_SIZE", "code": r"""CHUNK_SIZE = 1024

def split_into_chunks(data: bytes) -> list[bytes]:
    return [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]

def get_chunk_count(size: int) -> int:
    return -(-size // CHUNK_SIZE)"""},

    "unchecked_index_access": {"sig": "return user['emails'][0]", "code": r"""def get_primary_email(user: dict) -> str:
    emails = user.get('emails')
    if not emails:
        raise ValueError('user has no email addresses')
    return emails[0]"""},

    "async_fire_and_forget_lost": {"sig": "", "code": r"""import asyncio

_background_tasks: set = set()

async def handle_request(event: dict):
    task = asyncio.create_task(send_analytics(event))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return process(event)"""},

    "concatenate_strings_loop": {"sig": "row = row + field", "code": r"""def build_csv_row(fields: list[str]) -> str:
    return ','.join(fields)"""},

    "unbounded_recursion": {"sig": "if n == 0:", "code": r"""def count_down(n: int):
    if n <= 0:
        return
    print(n)
    count_down(n - 1)"""},

    "overwrite_param_before_use": {"sig": "record_id = str(record_id)", "code": r"""def update_record(record_id: int, data: dict) -> bool:
    existing = db.fetch(record_id)
    if not existing:
        return False
    db.update(record_id, data)
    return True"""},

    "global_keyword_missing": {"sig": "", "code": r"""_count = 0

def increment():
    global _count
    _count += 1

def get_count() -> int:
    return _count"""},

    "enumerate_wrong_start": {"sig": "enumerate(items):", "code": r"""def display_list(items: list) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f'{i}. {item}')
    return '\n'.join(lines)"""},

    "list_append_vs_extend": {"sig": "result.append(extra)", "code": r"""def merge_tags(base_tags: list, extra: list) -> list:
    result = base_tags.copy()
    result.extend(extra)
    return result"""},

    "sentinel_value_confusion": {"sig": "if idx:", "code": r"""def find_index(items: list, target) -> int:
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1

idx = find_index(items, val)
if idx != -1:
    print(items[idx])"""},

    "dict_get_none_default": {"sig": "cart.get('discount')\n", "code": r"""def apply_discount(cart: dict, promo_code: str) -> float:
    discount = cart.get('discount', 0)
    total = cart['total'] * (1 - discount)
    return total"""},

    "wrong_argument_order": {"sig": "timedelta(delay_seconds)", "code": r"""from datetime import timedelta

def schedule_retry(delay_seconds: int):
    delta = timedelta(seconds=delay_seconds)
    return get_now() + delta"""},

    "async_sleep_blocking": {"sig": "time.sleep(0.5)", "code": r"""import asyncio

async def rate_limited_fetch(url: str) -> str:
    await asyncio.sleep(0.5)
    return await fetch(url)"""},

    "format_string_wrong_type": {"sig": "{amount:d}", "code": r"""def format_price(amount: float, currency: str = 'USD') -> str:
    return f'{currency}: {amount:.2f}'"""},

    "dataclass_frozen_field": {"sig": "history: list = []", "code": r"""from dataclasses import dataclass, field

@dataclass
class Point:
    x: float
    y: float
    history: list = field(default_factory=list)

    def move(self, dx, dy):
        self.history.append((self.x, self.y))
        self.x += dx
        self.y += dy"""},

    "modulo_negative": {"sig": "return idx - size", "code": r"""def wrap_index(idx: int, size: int) -> int:
    return idx % size"""},

    # ── maintainability (26) ──
    "global_state_mutation": {"sig": "_registry = {}", "code": r"""def register(registry: dict, name: str, handler):
    registry[name] = handler

def process(registry: dict, name: str, data):
    return registry[name](data)"""},

    "n_plus_one_query": {"sig": "order['items'] = db.query(", "code": r"""def get_orders_with_items(user_id: int) -> list:
    orders = db.query('SELECT * FROM orders WHERE user_id=?', user_id)
    items = db.query('SELECT * FROM items WHERE order_id IN '
                     '(SELECT id FROM orders WHERE user_id=?)', user_id)
    by_order = {}
    for item in items:
        by_order.setdefault(item['order_id'], []).append(item)
    for order in orders:
        order['items'] = by_order.get(order['id'], [])
    return orders"""},

    "socket_not_closed": {"sig": "s = socket.socket()", "code": r"""import socket

def send_ping(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.connect((host, port))
        s.send(b'PING')
        return s.recv(4) == b'PONG'"""},

    "ignored_return_value": {"sig": "return True", "code": r"""def update_user_email(user_id: int, new_email: str):
    cursor = db.execute('UPDATE users SET email=? WHERE id=?', new_email, user_id)
    return cursor.rowcount > 0"""},

    "catch_and_ignore": {"sig": "        pass", "code": r"""import logging

def load_plugin(name: str):
    try:
        module = importlib.import_module(f'plugins.{name}')
        return module.init()
    except Exception:
        logging.exception('Failed to load plugin %r', name)
        return None"""},

    "string_format_inconsistency": {"sig": "'%s' % step2", "code": r"""def build_url(base: str, path: str, param: str) -> str:
    return f'{base}/{path}?q={param}'"""},

    "overlong_function": {"sig": "def validate_and_save_profile", "code": r"""def validate_profile(name, email, phone, bio):
    if len(name) < 2 or len(name) > 50:
        raise ValueError('name length')
    if '@' not in email:
        raise ValueError('bad email')
    if phone and not phone.replace('+','').replace('-','').isdigit():
        raise ValueError('bad phone')
    if len(bio or '') > 500:
        raise ValueError('bio too long')

def save_profile(user_id, profile: dict):
    validate_profile(profile['name'], profile['email'], profile.get('phone'), profile.get('bio'))
    db.update_profile(user_id, **profile)
    cache.invalidate(f'profile:{user_id}')"""},

    "todo_comment_blocking": {"sig": "# TODO: add brute-force protection", "code": r"""def authenticate(username: str, password: str) -> bool:
    if lockout.is_locked(username):
        return False
    user = db.get_user(username)
    if user is None:
        return False
    ok = check_password(password, user['pw_hash'])
    lockout.record_attempt(username, ok)
    return ok"""},

    "no_input_validation_public": {"sig": "", "code": r"""VALID_LEVELS = {logging.DEBUG, logging.INFO, logging.WARNING,
                logging.ERROR, logging.CRITICAL}

def set_log_level(level: int):
    if level not in VALID_LEVELS:
        raise ValueError(f'invalid log level: {level}')
    logging.root.setLevel(level)"""},

    "class_variable_vs_instance": {"sig": "    request_count = 0", "code": r"""class RequestTracker:
    def __init__(self):
        self.request_count = 0

    def track(self):
        self.request_count += 1
        return self.request_count"""},

    "unnecessary_else_after_return": {"sig": "    else:", "code": r"""def grade(score: int) -> str:
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    return 'C'"""},

    "file_open_no_encoding": {"sig": "open(path)", "code": r"""def read_text_file(path: str) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()"""},

    "chained_string_replace": {"sig": ".replace('  ', ' ')", "code": r"""import re

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text)"""},

    "global_mutable_config": {"sig": "CONFIG['debug'] = value", "code": r"""from types import MappingProxyType

_DEFAULTS = {
    'db_url': 'sqlite:///local.db',
    'debug': False,
}
CONFIG = MappingProxyType(_DEFAULTS)

def config_with_debug(value: bool) -> dict:
    return {**_DEFAULTS, 'debug': value}"""},

    "nested_list_comprehension_unreadable": {"sig": "return [cell for row in matrix", "code": r"""def flatten_matrix(matrix: list) -> list:
    cells = []
    for row in matrix:
        for cell in row:
            if cell is not None:
                cells.append(cell)
    return cells"""},

    "boolean_comparison_to_true": {"sig": "== True", "code": r"""def check_flag(config: dict) -> bool:
    return bool(config.get('enabled'))"""},

    "resource_leak_exception_path": {"sig": "f = open(path)", "code": r"""def process_file(path: str) -> str:
    with open(path) as f:
        data = f.read()
    return transform(data)"""},

    "print_to_stdout_in_lib": {"sig": "print(f'Risk score", "code": r"""import logging

logger = logging.getLogger(__name__)

def compute_risk_score(factors: list) -> float:
    score = sum(factors) / len(factors)
    logger.debug('Risk score computed: %.2f', score)
    return score"""},

    "test_without_assertion": {"sig": "print(user)", "code": r"""def test_create_user():
    user = create_user(name='Alice', email='a@b.com')
    assert user is not None
    assert user.name == 'Alice'
    assert user.email == 'a@b.com'"""},

    "catch_keyboardinterrupt": {"sig": "            pass", "code": r"""import logging

def run_forever():
    while True:
        try:
            process_next()
        except Exception:
            logging.exception('process_next failed; continuing')"""},

    "module_level_side_effect": {"sig": "\nlogging.basicConfig(level=logging.DEBUG)\n", "code": r"""import logging
import os

def setup_logging(log_dir: str = '/tmp/myapp'):
    logging.basicConfig(level=logging.DEBUG)
    os.makedirs(log_dir, exist_ok=True)

def get_logger():
    return logging.getLogger('myapp')"""},

    "constant_in_loop_condition": {"sig": "length = len(items)", "code": r"""def find_first(items: list, target: int) -> int:
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1"""},

    "lambda_instead_of_def": {"sig": "process = lambda", "code": r'''def process(data, threshold):
    """Return active items scoring above threshold."""
    return [
        item for item in data
        if item['score'] > threshold and item.get('active', False)
    ]'''},

    "sys_exit_in_library": {"sig": "sys.exit(1)", "code": r"""def load_required_config(path: str) -> dict:
    try:
        return load(path)
    except FileNotFoundError as e:
        raise RuntimeError(f'Config not found: {path}') from e"""},

    "inline_magic_string_comparison": {"sig": "elif event['type']", "code": r"""_HANDLERS = {
    'user_created': on_user_created,
    'user_deleted': on_user_deleted,
    'user_updated': on_user_updated,
}

def handle_event(event: dict):
    _HANDLERS[event['type']](event)"""},

    "wide_import_star": {"sig": "from os.path import *", "code": r"""from os.path import join
from datetime import date

def get_log_path(name: str) -> str:
    today = date.today().strftime('%Y%m%d')
    return join('/var/log', f'{name}_{today}.log')"""},
}

# ── Broken versions (s+) for the 26 clean tasks ──────────────────────────────
# Each plants exactly one flaw; category/desc/keywords describe the planted
# issue (the pair's scoring metadata), signature witnesses it in s+.

BREAKS: dict[str, dict] = {
    "clean_password_hash": {
        "category": "security", "severity": "critical",
        "desc": "Hardcoded static salt — identical hashes for identical passwords, rainbow-table attackable",
        "keywords": ["salt", "static", "hardcod", "rainbow", "unique", "random"],
        "sig": "'static-salt'",
        "code": r"""import secrets
import hashlib

def hash_password(password: str) -> tuple[str, str]:
    salt = 'static-salt'
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 260_000
    )
    return salt, hashed.hex()"""},

    "clean_dataclass": {
        "category": "correctness", "severity": "medium",
        "desc": "Default value type mismatch — port annotated int but defaults to string '8080'",
        "keywords": ["type", "str", "int", "mismatch", "default", "annotation"],
        "sig": "'8080'",
        "code": r"""from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    host: str
    port: int = '8080'
    tags: list[str] = field(default_factory=list)
    timeout: Optional[float] = None"""},

    "clean_rate_limiter": {
        "category": "correctness", "severity": "medium",
        "desc": "Wall-clock time.time() used for the rate window — clock adjustments (NTP/DST) break limiting; use monotonic",
        "keywords": ["monotonic", "wall", "clock", "time.time", "jump", "ntp"],
        "sig": "time.time()",
        "code": r"""import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period    = period
        self.calls: deque = deque()

    def is_allowed(self) -> bool:
        now = time.time()
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False"""},

    "clean_immutable_config": {
        "category": "security", "severity": "critical",
        "desc": "Hardcoded database password committed in source",
        "keywords": ["hardcod", "password", "credential", "secret", "environ", "source"],
        "sig": "'hunter2'",
        "code": r"""from typing import NamedTuple

class DBConfig(NamedTuple):
    host: str
    port: int
    name: str
    password: str = 'hunter2'
    pool_size: int = 5

PROD = DBConfig(host='db.prod.internal', port=5432, name='app')"""},

    "clean_lru_cache": {
        "category": "maintainability", "severity": "low",
        "desc": "Unbounded lru_cache — maxsize=None grows memory without limit",
        "keywords": ["unbounded", "maxsize", "memory", "cache", "grow", "limit"],
        "sig": "maxsize=None",
        "code": r"""from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)"""},

    "clean_dataclass_frozen": {
        "category": "correctness", "severity": "medium",
        "desc": "Currency mismatch guard removed — adding USD and EUR silently produces a wrong Money value",
        "keywords": ["currency", "mismatch", "check", "guard", "silent", "wrong"],
        "sig": "",
        "code": r"""from dataclasses import dataclass, field

@dataclass(frozen=True)
class Money:
    amount: int
    currency: str

    def __add__(self, other: 'Money') -> 'Money':
        return Money(self.amount + other.amount, self.currency)"""},

    "clean_enum_methods": {
        "category": "correctness", "severity": "medium",
        "desc": "Boundary bug — strict < excludes status 200 from is_success",
        "keywords": ["boundary", "200", "off.by.one", "inclusive", "range", "exclude"],
        "sig": "200 < self.value",
        "code": r"""from enum import Enum

class HttpStatus(Enum):
    OK = 200
    NOT_FOUND = 404
    SERVER_ERROR = 500

    def is_success(self) -> bool:
        return 200 < self.value < 300

    def is_error(self) -> bool:
        return self.value >= 400"""},

    "clean_abc_interface": {
        "category": "maintainability", "severity": "low",
        "desc": "@abstractmethod removed — subclasses silently inherit no-op serialize/deserialize instead of being forced to implement",
        "keywords": ["abstract", "enforce", "interface", "no-op", "silent", "contract"],
        "sig": "",
        "code": r"""from abc import ABC

class Serializer(ABC):
    def serialize(self, obj: dict) -> bytes:
        ...

    def deserialize(self, data: bytes) -> dict:
        ..."""},

    "clean_context_manager_class": {
        "category": "correctness", "severity": "medium",
        "desc": "__exit__ returns True — silently suppresses every exception raised inside the with block",
        "keywords": ["suppress", "exit", "exception", "swallow", "true", "silent"],
        "sig": "return True",
        "code": r"""class Timer:
    def __enter__(self):
        import time
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        import time
        self.elapsed = time.perf_counter() - self._start
        return True"""},

    "clean_functools_partial": {
        "category": "maintainability", "severity": "low",
        "desc": "Named lambdas assigned to variables instead of partial/def — PEP 8 violation, no docstrings",
        "keywords": ["lambda", "def", "partial", "pep8", "named", "readab"],
        "sig": "lambda obj:",
        "code": r"""import json

compact_json = lambda obj: json.dumps(obj, separators=(',', ':'), sort_keys=True)
pretty_json  = lambda obj: json.dumps(obj, indent=2, sort_keys=True)"""},

    "clean_walrus_operator": {
        "category": "correctness", "severity": "medium",
        "desc": "Missing None check — m.group(1) raises AttributeError when the pattern does not match",
        "keywords": ["none", "attributeerror", "match", "check", "group", "guard"],
        "sig": "",
        "code": r"""import re

def extract_version(text: str) -> str | None:
    m = re.search(r'v(\d+\.\d+\.\d+)', text)
    return m.group(1)"""},

    "clean_named_tuple_return": {
        "category": "correctness", "severity": "medium",
        "desc": "split instead of rsplit on ':' — IPv6 host:port strings parsed at the wrong colon",
        "keywords": ["rsplit", "ipv6", "colon", "split", "parse", "wrong"],
        "sig": ".split(':', 1)",
        "code": r"""from typing import NamedTuple

class ParseResult(NamedTuple):
    host: str
    port: int
    path: str

def parse_endpoint(endpoint: str) -> ParseResult:
    host, rest = endpoint.split('/', 1)
    host, port_str = host.split(':', 1)
    return ParseResult(host=host, port=int(port_str), path='/' + rest)"""},

    "clean_cached_property": {
        "category": "maintainability", "severity": "low",
        "desc": "cached_property replaced by plain property — word_count recomputed on every access",
        "keywords": ["cache", "recomput", "property", "every access", "inefficien", "memo"],
        "sig": "@property\n",
        "code": r"""class Document:
    def __init__(self, text: str):
        self.text = text

    @property
    def word_count(self) -> int:
        return len(self.text.split())"""},

    "clean_dataclass_post_init": {
        "category": "correctness", "severity": "medium",
        "desc": "Email normalised to uppercase — case-sensitive downstream systems break; should be lower()",
        "keywords": ["lower", "upper", "normali", "case", "wrong", "email"],
        "sig": ".upper()",
        "code": r"""from dataclasses import dataclass

@dataclass
class EmailAddress:
    value: str

    def __post_init__(self):
        self.value = self.value.strip().upper()
        if '@' not in self.value:
            raise ValueError(f'Invalid email: {self.value!r}')"""},

    "clean_async_context_manager": {
        "category": "maintainability", "severity": "low",
        "desc": "close not in finally — the session leaks whenever the with-body raises",
        "keywords": ["finally", "leak", "close", "exception", "guarantee", "resource"],
        "sig": "",
        "code": r"""from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_session(client):
    session = await client.open_session()
    yield session
    await session.close()"""},

    "clean_heapq_nlargest": {
        "category": "correctness", "severity": "medium",
        "desc": "nsmallest returns the lowest scores instead of the top n",
        "keywords": ["nsmallest", "nlargest", "wrong", "lowest", "top", "direction"],
        "sig": "nsmallest",
        "code": r"""import heapq

def top_n_scores(scores: list[int], n: int) -> list[int]:
    if n >= len(scores):
        return sorted(scores, reverse=True)
    return heapq.nsmallest(n, scores)"""},

    "clean_parameterized_fixture": {
        "category": "maintainability", "severity": "low",
        "desc": "Parametrized coverage replaced by a single print-only test — no assertion, always passes",
        "keywords": ["assert", "test", "missing", "always pass", "print", "coverage"],
        "sig": "print(is_zero",
        "code": r"""def test_is_zero():
    print(is_zero(0))"""},

    "clean_decimal_currency": {
        "category": "correctness", "severity": "medium",
        "desc": "Float used for currency arithmetic — binary rounding errors accumulate; use Decimal",
        "keywords": ["float", "decimal", "currency", "rounding", "precision", "money"],
        "sig": "float",
        "code": r"""def apply_tax(amount: float, rate: float) -> float:
    tax = round(amount * rate, 2)
    return amount + tax"""},

    "clean_thread_local": {
        "category": "correctness", "severity": "medium",
        "desc": "Module-level shared dict — request context leaks across threads",
        "keywords": ["thread", "shared", "local", "leak", "context", "race"],
        "sig": "_context = {}",
        "code": r"""_context = {}

def get_request_context() -> dict:
    return _context"""},

    "clean_contextvar": {
        "category": "correctness", "severity": "medium",
        "desc": "Global variable instead of ContextVar — concurrent async tasks overwrite each other's request id",
        "keywords": ["contextvar", "global", "async", "overwrite", "scope", "race"],
        "sig": "_request_id = ''",
        "code": r"""_request_id = ''

def set_request_id(rid: str):
    global _request_id
    _request_id = rid

def get_request_id() -> str:
    return _request_id"""},

    "clean_slots_dataclass": {
        "category": "correctness", "severity": "medium",
        "desc": "Latitude and longitude swapped in to_tuple — silently wrong coordinates",
        "keywords": ["swap", "lat", "lon", "order", "wrong", "coordinate"],
        "sig": "(self.lon, self.lat",
        "code": r"""from dataclasses import dataclass

@dataclass(slots=True)
class Coordinate:
    lat: float
    lon: float
    alt: float = 0.0

    def to_tuple(self) -> tuple[float, float, float]:
        return (self.lon, self.lat, self.alt)"""},

    "clean_abstractproperty": {
        "category": "maintainability", "severity": "low",
        "desc": "Deprecated abstractproperty API — removed in modern Python style; use @property + @abstractmethod",
        "keywords": ["abstractproperty", "deprecat", "abstractmethod", "property", "api", "old"],
        "sig": "abstractproperty",
        "code": r"""from abc import ABC, abstractproperty

class Shape(ABC):
    @abstractproperty
    def area(self) -> float:
        ...

    @abstractproperty
    def perimeter(self) -> float:
        ..."""},

    "clean_class_method_factory": {
        "category": "correctness", "severity": "medium",
        "desc": "Wrong hex slice offsets — blue channel parsed from overlapping digits [3:5]",
        "keywords": ["slice", "offset", "hex", "wrong", "overlap", "channel"],
        "sig": "[3:5]",
        "code": r"""from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Color:
    r: int
    g: int
    b: int

    @classmethod
    def from_hex(cls, hex_str: str) -> Color:
        hex_str = hex_str.lstrip('#')
        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[3:5], 16)
        return cls(r, g, b)"""},

    "clean_total_ordering": {
        "category": "correctness", "severity": "medium",
        "desc": "__lt__ implemented as <= — total_ordering derives inconsistent comparisons (a<b and b<a both true on equal versions)",
        "keywords": ["strict", "<=", "ordering", "inconsisten", "comparison", "wrong"],
        "sig": "<= other.version",
        "code": r"""from functools import total_ordering

@total_ordering
class Version:
    def __init__(self, major: int, minor: int, patch: int):
        self.version = (major, minor, patch)

    def __eq__(self, other) -> bool:
        return self.version == other.version

    def __lt__(self, other) -> bool:
        return self.version <= other.version"""},

    "clean_suppress_context": {
        "category": "correctness", "severity": "medium",
        "desc": "suppress(Exception) hides every error, not just the intended FileNotFoundError",
        "keywords": ["broad", "suppress", "exception", "swallow", "narrow", "hide"],
        "sig": "suppress(Exception)",
        "code": r"""from contextlib import suppress

def safe_delete(path: str) -> bool:
    from pathlib import Path
    with suppress(Exception):
        Path(path).unlink()
        return True
    return False"""},

    "clean_dataclass_comparison": {
        "category": "correctness", "severity": "medium",
        "desc": "Field order makes order=True sort by name alphabetically, not by priority level",
        "keywords": ["field order", "sort", "order=true", "priority", "wrong", "compare"],
        "sig": "    name: str\n    level: int",
        "code": r"""from dataclasses import dataclass

@dataclass(order=True)
class Priority:
    name: str
    level: int

HIGH   = Priority(name='high', level=1)
MEDIUM = Priority(name='medium', level=2)
LOW    = Priority(name='low', level=3)"""},
}


def build_pairs() -> list[dict]:
    pool = {t["id"]: t for t in recover_complement()}
    pairs = []
    for tid, task in pool.items():
        if task["has_issue"]:
            fix = FIXES[tid]
            pairs.append({
                "pair_id": f"fix_{tid}",
                "base_task_id": tid,
                "direction": "fix",
                "category": task["issue_type"],
                "severity": task["severity"],
                "issue_desc": task["issue_desc"],
                "issue_keywords": task["issue_keywords"],
                "s_plus_code": task["code"],
                "s_minus_code": fix["code"],
                "signature": fix["sig"],
                "source_model": "claude-fable-5 (hand-authored, 2026-07-29)",
            })
        else:
            brk = BREAKS[tid]
            pairs.append({
                "pair_id": f"break_{tid}",
                "base_task_id": tid,
                "direction": "break",
                "category": brk["category"],
                "severity": brk["severity"],
                "issue_desc": brk["desc"],
                "issue_keywords": brk["keywords"],
                "s_plus_code": brk["code"],
                "s_minus_code": task["code"],
                "signature": brk["sig"],
                "source_model": "claude-fable-5 (hand-authored, 2026-07-29)",
            })
    return pairs


def write_audit_sheet(pairs: list[dict], errors_by_pair: dict[str, list[str]]) -> None:
    with open(AUDIT, "w") as f:
        f.write("# Pair audit sheet — pairs_v1 draft\n\n"
                "Authored by Claude Fable 5 (2026-07-29). For each pair, the diff "
                "removes (fix) or plants (break) exactly the named issue. Pre-marked "
                "`ok` by the author; flip to `REJECT: <reason>` where you disagree, "
                "then freeze with `python run_charter.py freeze-pairs`.\n")
        for p in pairs:
            errs = errors_by_pair.get(p["pair_id"], [])
            f.write(f"\n---\n\n## {p['pair_id']}  ({p['category']}, {p['direction']})\n\n"
                    f"**Issue:** {p['issue_desc']}\n\n")
            if errs:
                f.write("**VALIDATION ERRORS:** " + "; ".join(errs) + "\n\n")
            diff = difflib.unified_diff(
                p["s_minus_code"].splitlines(), p["s_plus_code"].splitlines(),
                fromfile="s- (clean)", tofile="s+ (flawed)", lineterm="")
            f.write("```diff\n" + "\n".join(diff) + "\n```\n\n")
            f.write("Audit: ok\n")


def main() -> None:
    if FROZEN.exists():
        raise SystemExit(f"{FROZEN} is frozen — a new fixture is a new version "
                         f"(pairs_v2), not an overwrite.")
    pairs = build_pairs()
    errors_by_pair = {}
    for p in pairs:
        errs = validate_pair(p)
        if errs:
            errors_by_pair[p["pair_id"]] = errs
    DRAFT.write_text(json.dumps(pairs, indent=1))
    write_audit_sheet(pairs, errors_by_pair)
    n_err = sum(len(v) for v in errors_by_pair.values())
    print(f"{len(pairs)} pairs written to {DRAFT.name}; "
          f"{len(errors_by_pair)} pairs with {n_err} validation errors")
    if errors_by_pair:
        for pid, errs in errors_by_pair.items():
            print(f"  {pid}: {errs}")


if __name__ == "__main__":
    main()
