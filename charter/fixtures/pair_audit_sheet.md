# Pair audit sheet — pairs_v1 draft

Authored by Claude Fable 5 (2026-07-29). For each pair, the diff removes (fix) or plants (break) exactly the named issue. Pre-marked `ok` by the author; flip to `REJECT: <reason>` where you disagree, then freeze with `python run_charter.py freeze-pairs`.

---

## fix_timing_attack  (security, fix)

**Issue:** Timing attack — string equality leaks token length via early exit

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,2 @@
-import hmac
-
 def verify_token(user_token: str, stored_token: str) -> bool:
-    return hmac.compare_digest(user_token, stored_token)
+    return user_token == stored_token
```

Audit: ok

---

## fix_weak_prng_seeded  (security, fix)

**Issue:** PRNG seeded with timestamp — predictable within a small window

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,6 @@
-import secrets
+import random
+import time
 
 def generate_session_id():
-    return secrets.token_hex(8)
+    random.seed(int(time.time()))
+    return hex(random.getrandbits(64))
```

Audit: ok

---

## fix_open_redirect  (security, fix)

**Issue:** Open redirect — attacker can redirect to arbitrary external URL

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -2,6 +2,4 @@
 
 def login_redirect():
     next_url = request.args.get('next', '/')
-    if not next_url.startswith('/') or next_url.startswith('//'):
-        next_url = '/'
     return redirect(next_url)
```

Audit: ok

---

## fix_xxe_lxml  (security, fix)

**Issue:** XXE injection — default lxml parser resolves external entities

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
 from lxml import etree
 
 def parse_config(xml_data: str):
-    parser = etree.XMLParser(resolve_entities=False, no_network=True)
+    parser = etree.XMLParser()
     return etree.fromstring(xml_data.encode(), parser)
```

Audit: ok

---

## fix_global_state_mutation  (maintainability, fix)

**Issue:** Mutable global state makes testing and concurrency difficult

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,7 @@
-def register(registry: dict, name: str, handler):
-    registry[name] = handler
+_registry = {}
 
-def process(registry: dict, name: str, data):
-    return registry[name](data)
+def register(name: str, handler):
+    _registry[name] = handler
+
+def process(name: str, data):
+    return _registry[name](data)
```

Audit: ok

---

## break_clean_password_hash  (security, break)

**Issue:** Hardcoded static salt — identical hashes for identical passwords, rainbow-table attackable

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -2,7 +2,7 @@
 import hashlib
 
 def hash_password(password: str) -> tuple[str, str]:
-    salt = secrets.token_hex(16)
+    salt = 'static-salt'
     hashed = hashlib.pbkdf2_hmac(
         "sha256", password.encode(), salt.encode(), 260_000
     )
```

Audit: ok

---

## break_clean_dataclass  (correctness, break)

**Issue:** Default value type mismatch — port annotated int but defaults to string '8080'

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -4,6 +4,6 @@
 @dataclass
 class Config:
     host: str
-    port: int = 8080
+    port: int = '8080'
     tags: list[str] = field(default_factory=list)
     timeout: Optional[float] = None
```

Audit: ok

---

## break_clean_rate_limiter  (correctness, break)

**Issue:** Wall-clock time.time() used for the rate window — clock adjustments (NTP/DST) break limiting; use monotonic

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -8,7 +8,7 @@
         self.calls: deque = deque()
 
     def is_allowed(self) -> bool:
-        now = time.monotonic()
+        now = time.time()
         while self.calls and self.calls[0] < now - self.period:
             self.calls.popleft()
         if len(self.calls) < self.max_calls:
```

Audit: ok

---

## break_clean_immutable_config  (security, break)

**Issue:** Hardcoded database password committed in source

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -4,6 +4,7 @@
     host: str
     port: int
     name: str
+    password: str = 'hunter2'
     pool_size: int = 5
 
 PROD = DBConfig(host='db.prod.internal', port=5432, name='app')
```

Audit: ok

---

## fix_pickle_deserialization  (security, fix)

**Issue:** Arbitrary code execution via pickle.loads on attacker-controlled input

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,6 +1,6 @@
-import json
+import pickle
 import base64
 
 def load_session(cookie_value: str):
     data = base64.b64decode(cookie_value)
-    return json.loads(data)
+    return pickle.loads(data)
```

Audit: ok

---

## fix_ssti_jinja2  (security, fix)

**Issue:** Server-side template injection — f-string builds template from user input before rendering

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -2,5 +2,5 @@
 
 def render_greeting(name: str) -> str:
     env = Environment()
-    template = env.from_string('Hello {{ name }}')
+    template = env.from_string(f'Hello {{ name }}')
     return template.render(name=name)
```

Audit: ok

---

## fix_xss_flask_response  (security, fix)

**Issue:** Reflected XSS — user-supplied query injected directly into HTML response

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,7 +1,6 @@
 from flask import request, Response
-from markupsafe import escape
 
 def search_results():
     query = request.args.get('q', '')
-    html = f'<h1>Results for: {escape(query)}</h1>'
+    html = f'<h1>Results for: {query}</h1>'
     return Response(html, mimetype='text/html')
```

Audit: ok

---

## fix_weak_md5_password  (security, fix)

**Issue:** MD5 is cryptographically broken and unsalted — trivially reversed via rainbow tables

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,7 +1,4 @@
 import hashlib
-import secrets
 
 def store_password(password: str) -> str:
-    salt = secrets.token_hex(16)
-    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260_000)
-    return f'{salt}${hashed.hex()}'
+    return hashlib.md5(password.encode()).hexdigest()
```

Audit: ok

---

## fix_insecure_cookie_flags  (security, fix)

**Issue:** Session cookie missing HttpOnly, Secure, and SameSite flags — vulnerable to XSS theft and CSRF

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
 from flask import make_response
 
 def set_session_cookie(resp, session_id: str):
-    resp.set_cookie('session', session_id, httponly=True, secure=True, samesite='Lax')
+    resp.set_cookie('session', session_id)
     return resp
```

Audit: ok

---

## fix_hardcoded_jwt_secret  (security, fix)

**Issue:** Hardcoded JWT secret in source code — rotatable only by redeployment, leaked in version control

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,7 +1,6 @@
-import os
 import jwt
 
-SECRET = os.environ['JWT_SECRET']
+SECRET = 'dev-secret-key-change-in-prod'
 
 def issue_token(user_id: int) -> str:
     return jwt.encode({'user': user_id}, SECRET, algorithm='HS256')
```

Audit: ok

---

## fix_timing_attack_login  (security, fix)

**Issue:** Timing attack on password comparison — early exit leaks information about correct prefix

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,3 @@
-import hmac
-
 def check_admin_password(entered: str) -> bool:
     correct = load_admin_password_hash()
-    return hmac.compare_digest(entered, correct)
+    return entered == correct
```

Audit: ok

---

## fix_nosql_injection_pymongo  (security, fix)

**Issue:** NoSQL injection — dict values can be operator dicts like {'$gt': ''} to bypass auth

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,7 +1,5 @@
 from pymongo import MongoClient
 
 def find_user(username: str, password: str):
-    if not isinstance(username, str) or not isinstance(password, str):
-        return None
     db = MongoClient()['app']
     return db.users.find_one({'username': username, 'password': password})
```

Audit: ok

---

## fix_insecure_deserialization_marshal  (security, fix)

**Issue:** marshal.loads on untrusted data allows arbitrary code execution via crafted bytecode

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,4 @@
-import json
+import marshal
 
 def restore_state(blob: bytes):
-    return json.loads(blob.decode())
+    return marshal.loads(blob)
```

Audit: ok

---

## fix_email_header_injection  (security, fix)

**Issue:** Email header injection — newline in to_addr or subject lets attacker add arbitrary headers

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,9 +1,6 @@
 import smtplib
 
-def _strip_crlf(value: str) -> str:
-    return value.replace('\r', '').replace('\n', '')
-
 def send_notification(to_addr: str, subject: str, body: str):
-    msg = f'To: {_strip_crlf(to_addr)}\nSubject: {_strip_crlf(subject)}\n\n{body}'
+    msg = f'To: {to_addr}\nSubject: {subject}\n\n{body}'
     with smtplib.SMTP('localhost') as s:
         s.sendmail('noreply@app.com', to_addr, msg)
```

Audit: ok

---

## fix_secret_in_url  (security, fix)

**Issue:** API key in URL query string — logged in server access logs, referrer headers, browser history

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,6 +1,5 @@
 import requests
 
 def call_analytics(api_key: str, event: str):
-    url = 'https://analytics.internal/track'
-    return requests.get(url, params={'event': event},
-                        headers={'X-API-Key': api_key})
+    url = f'https://analytics.internal/track?key={api_key}&event={event}'
+    return requests.get(url)
```

Audit: ok

---

## fix_reflected_user_input_log  (security, fix)

**Issue:** Log injection — newlines in user_data allow forging fake log entries

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -3,6 +3,5 @@
 logger = logging.getLogger(__name__)
 
 def process_input(user_data: str):
-    safe = user_data.replace('\r', '\\r').replace('\n', '\\n')
-    logger.info('Processing input: %s', safe)
+    logger.info(f'Processing input: {user_data}')
     return user_data.strip()
```

Audit: ok

---

## fix_permissive_cors  (security, fix)

**Issue:** CORS wildcard with credentials=True is disallowed by spec and exposes authenticated endpoints cross-origin

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -2,4 +2,4 @@
 from flask_cors import CORS
 
 app = Flask(__name__)
-CORS(app, origins=['https://app.example.com'], supports_credentials=True)
+CORS(app, origins='*', supports_credentials=True)
```

Audit: ok

---

## fix_sql_like_injection  (security, fix)

**Issue:** SQL injection via LIKE clause string interpolation — same risk as standard SQLi

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,3 +1,3 @@
 def search_products(keyword: str) -> list:
-    query = "SELECT * FROM products WHERE name LIKE ?"
-    return db.execute(query, (f'%{keyword}%',)).fetchall()
+    query = f"SELECT * FROM products WHERE name LIKE '%{keyword}%'"
+    return db.execute(query).fetchall()
```

Audit: ok

---

## fix_rce_via_assert  (security, fix)

**Issue:** assert removed by -O flag in production — security check silently disappears

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,6 +1,5 @@
 def safe_divide(a, b):
-    if b == 0:
-        raise ValueError('division by zero')
+    assert b != 0, 'division by zero'
     return a / b
 
 # Production deployment runs with python -O flag
```

Audit: ok

---

## fix_xxe_stdlib  (security, fix)

**Issue:** XXE via minidom.parseString — resolves external entities by default in older Python

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
-from defusedxml.minidom import parseString
+from xml.dom import minidom
 
 def parse_user_data(xml_string: str):
-    doc = parseString(xml_string)
+    doc = minidom.parseString(xml_string)
     return doc.getElementsByTagName('user')[0].firstChild.nodeValue
```

Audit: ok

---

## fix_token_stored_localstorage  (security, fix)

**Issue:** Auth token in localStorage is accessible to XSS — prefer HttpOnly cookie

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,9 +1,7 @@
 # Frontend JS snippet (called from Python-rendered template)
 def render_login_success(token: str) -> str:
-    # Token is delivered via an HttpOnly, Secure cookie set server-side;
-    # nothing readable by page scripts is emitted here.
-    return """
+    return f"""
     <script>
-    window.location.replace('/dashboard');
+    localStorage.setItem('auth_token', '{token}');
     </script>
 """
```

Audit: ok

---

## fix_sql_order_by_injection  (security, fix)

**Issue:** SQL injection via ORDER BY clause — column and direction not validated against whitelist

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,8 +1,3 @@
-ALLOWED_COLS = {'name', 'email', 'created'}
-
 def list_users(sort_col: str = 'name', sort_dir: str = 'ASC') -> list:
-    if sort_col not in ALLOWED_COLS:
-        sort_col = 'name'
-    sort_dir = 'DESC' if str(sort_dir).upper() == 'DESC' else 'ASC'
     query = f'SELECT * FROM users ORDER BY {sort_col} {sort_dir}'
     return db.execute(query).fetchall()
```

Audit: ok

---

## fix_unsafe_redirect_after_post  (security, fix)

**Issue:** Open redirect via Referer header — attacker-controlled page sets Referer to phishing URL

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -2,4 +2,5 @@
 
 def handle_form():
     process(request.form)
-    return redirect('/')
+    next_url = request.referrer or '/'
+    return redirect(next_url)
```

Audit: ok

---

## fix_s3_presigned_url_overexposed  (security, fix)

**Issue:** 7-day presigned URL expiry is excessive — leaked URLs give long-term access to private objects

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -5,5 +5,5 @@
     return s3.generate_presigned_url(
         'get_object',
         Params={'Bucket': bucket, 'Key': key},
-        ExpiresIn=900  # 15 minutes
+        ExpiresIn=604800  # 7 days
     )
```

Audit: ok

---

## fix_naive_datetime_comparison  (correctness, fix)

**Issue:** Timezone-naive comparison — mixes naive and aware datetimes if expiry is timezone-aware

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,4 @@
-from datetime import datetime, timezone
+from datetime import datetime
 
 def is_expired(expiry: datetime) -> bool:
-    return datetime.now(timezone.utc) > expiry
+    return datetime.now() > expiry
```

Audit: ok

---

## fix_integer_division_python2_style  (correctness, fix)

**Issue:** Empty list causes ZeroDivisionError with no guard; also silently wrong when len is 0

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,2 @@
 def average(values: list) -> float:
-    if not values:
-        return 0.0
     return sum(values) / len(values)
```

Audit: ok

---

## fix_missing_return_recursive  (correctness, fix)

**Issue:** Missing return statement — function always returns None instead of the flattened list

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -5,4 +5,3 @@
             result.extend(flatten(item))
         else:
             result.append(item)
-    return result
```

Audit: ok

---

## fix_thread_unsafe_counter  (correctness, fix)

**Issue:** Read-modify-write on self._value is not atomic under GIL contention — lost updates possible

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -3,11 +3,9 @@
 class Counter:
     def __init__(self):
         self._value = 0
-        self._lock = threading.Lock()
 
     def increment(self):
-        with self._lock:
-            self._value += 1
+        self._value += 1
 
     def get(self):
         return self._value
```

Audit: ok

---

## fix_sort_wrong_key  (correctness, fix)

**Issue:** Sort ascending returns n lowest scorers, not highest — should sort reverse=True

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,3 +1,3 @@
 def top_scorers(players: list[dict], n: int) -> list[dict]:
-    players.sort(key=lambda p: p['score'], reverse=True)
+    players.sort(key=lambda p: p['score'])
     return players[:n]
```

Audit: ok

---

## fix_empty_except_continue  (correctness, fix)

**Issue:** Silently drops malformed records — caller gets partial results with no indication of skipped items

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,10 +1,8 @@
-import logging
-
 def parse_all(records: list) -> list:
     results = []
     for rec in records:
         try:
             results.append(parse(rec))
         except ValueError:
-            logging.warning('Skipping malformed record: %r', rec)
+            continue
     return results
```

Audit: ok

---

## fix_copy_shallow_nested  (correctness, fix)

**Issue:** Shallow copy — nested dicts/lists still shared, mutations propagate to original

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,2 @@
-import copy
-
 def clone_config(config: dict) -> dict:
-    return copy.deepcopy(config)
+    return config.copy()
```

Audit: ok

---

## fix_exclusive_range_boundary  (correctness, fix)

**Issue:** Chunk count wrong when size is not a multiple of CHUNK_SIZE — ceiling division needed

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -4,4 +4,4 @@
     return [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
 
 def get_chunk_count(size: int) -> int:
-    return -(-size // CHUNK_SIZE)
+    return size // CHUNK_SIZE
```

Audit: ok

---

## fix_unchecked_index_access  (correctness, fix)

**Issue:** IndexError when emails list is empty — no guard for missing or empty list

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,2 @@
 def get_primary_email(user: dict) -> str:
-    emails = user.get('emails')
-    if not emails:
-        raise ValueError('user has no email addresses')
-    return emails[0]
+    return user['emails'][0]
```

Audit: ok

---

## fix_async_fire_and_forget_lost  (correctness, fix)

**Issue:** Unawaited task reference lost — GC can cancel the task before it completes

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,9 +1,5 @@
 import asyncio
 
-_background_tasks: set = set()
-
 async def handle_request(event: dict):
-    task = asyncio.create_task(send_analytics(event))
-    _background_tasks.add(task)
-    task.add_done_callback(_background_tasks.discard)
+    asyncio.create_task(send_analytics(event))
     return process(event)
```

Audit: ok

---

## fix_concatenate_strings_loop  (correctness, fix)

**Issue:** O(n²) string concatenation in loop — use ','.join(fields) instead

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,2 +1,7 @@
 def build_csv_row(fields: list[str]) -> str:
-    return ','.join(fields)
+    row = ''
+    for i, field in enumerate(fields):
+        if i > 0:
+            row = row + ','
+        row = row + field
+    return row
```

Audit: ok

---

## fix_unbounded_recursion  (correctness, fix)

**Issue:** No guard for negative n — count_down(-1) recurses indefinitely until RecursionError

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
 def count_down(n: int):
-    if n <= 0:
+    if n == 0:
         return
     print(n)
     count_down(n - 1)
```

Audit: ok

---

## fix_overwrite_param_before_use  (correctness, fix)

**Issue:** record_id overwritten from int to str — if db.fetch expects int, the type conversion breaks lookup

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,5 @@
 def update_record(record_id: int, data: dict) -> bool:
+    record_id = str(record_id)
     existing = db.fetch(record_id)
     if not existing:
         return False
```

Audit: ok

---

## fix_global_keyword_missing  (correctness, fix)

**Issue:** UnboundLocalError — _count += 1 creates local variable but reads before assignment without global keyword

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,7 +1,6 @@
 _count = 0
 
 def increment():
-    global _count
     _count += 1
 
 def get_count() -> int:
```

Audit: ok

---

## fix_enumerate_wrong_start  (correctness, fix)

**Issue:** enumerate starts at 0 but display lists conventionally start at 1 — use enumerate(items, 1)

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
 def display_list(items: list) -> str:
     lines = []
-    for i, item in enumerate(items, 1):
+    for i, item in enumerate(items):
         lines.append(f'{i}. {item}')
     return '\n'.join(lines)
```

Audit: ok

---

## fix_list_append_vs_extend  (correctness, fix)

**Issue:** append(extra) nests the list — creates [[...]] instead of flat merge; use extend

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,4 @@
 def merge_tags(base_tags: list, extra: list) -> list:
     result = base_tags.copy()
-    result.extend(extra)
+    result.append(extra)
     return result
```

Audit: ok

---

## fix_sentinel_value_confusion  (correctness, fix)

**Issue:** if idx: treats index 0 as falsy — first element match silently skipped

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -5,5 +5,5 @@
     return -1
 
 idx = find_index(items, val)
-if idx != -1:
+if idx:
     print(items[idx])
```

Audit: ok

---

## fix_dict_get_none_default  (correctness, fix)

**Issue:** cart.get('discount') returns None when key missing — multiplying by None raises TypeError

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,4 @@
 def apply_discount(cart: dict, promo_code: str) -> float:
-    discount = cart.get('discount', 0)
+    discount = cart.get('discount')
     total = cart['total'] * (1 - discount)
     return total
```

Audit: ok

---

## fix_wrong_argument_order  (correctness, fix)

**Issue:** timedelta(n) sets days=n, not seconds — use timedelta(seconds=delay_seconds)

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
 from datetime import timedelta
 
 def schedule_retry(delay_seconds: int):
-    delta = timedelta(seconds=delay_seconds)
+    delta = timedelta(delay_seconds)
     return get_now() + delta
```

Audit: ok

---

## fix_async_sleep_blocking  (correctness, fix)

**Issue:** time.sleep in async function blocks the event loop — use await asyncio.sleep(0.5)

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
-import asyncio
+import asyncio, time
 
 async def rate_limited_fetch(url: str) -> str:
-    await asyncio.sleep(0.5)
+    time.sleep(0.5)
     return await fetch(url)
```

Audit: ok

---

## fix_format_string_wrong_type  (correctness, fix)

**Issue:** :d format specifier requires integer — raises ValueError for float amount

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,2 +1,2 @@
 def format_price(amount: float, currency: str = 'USD') -> str:
-    return f'{currency}: {amount:.2f}'
+    return f'{currency}: {amount:d}'
```

Audit: ok

---

## fix_dataclass_frozen_field  (correctness, fix)

**Issue:** Mutable list default in dataclass field — all Point instances share same history list

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,10 +1,10 @@
-from dataclasses import dataclass, field
+from dataclasses import dataclass
 
 @dataclass
 class Point:
     x: float
     y: float
-    history: list = field(default_factory=list)
+    history: list = []
 
     def move(self, dx, dy):
         self.history.append((self.x, self.y))
```

Audit: ok

---

## fix_modulo_negative  (correctness, fix)

**Issue:** Doesn't handle idx > 2*size or negative idx — use idx % size instead

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,2 +1,4 @@
 def wrap_index(idx: int, size: int) -> int:
-    return idx % size
+    if idx >= size:
+        return idx - size
+    return idx
```

Audit: ok

---

## fix_n_plus_one_query  (maintainability, fix)

**Issue:** N+1 query problem — one extra DB query per order; use JOIN or batch fetch

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,10 +1,5 @@
 def get_orders_with_items(user_id: int) -> list:
     orders = db.query('SELECT * FROM orders WHERE user_id=?', user_id)
-    items = db.query('SELECT * FROM items WHERE order_id IN '
-                     '(SELECT id FROM orders WHERE user_id=?)', user_id)
-    by_order = {}
-    for item in items:
-        by_order.setdefault(item['order_id'], []).append(item)
     for order in orders:
-        order['items'] = by_order.get(order['id'], [])
+        order['items'] = db.query('SELECT * FROM items WHERE order_id=?', order['id'])
     return orders
```

Audit: ok

---

## fix_socket_not_closed  (maintainability, fix)

**Issue:** Socket never closed — resource leak on every call, especially on exception path

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,7 +1,7 @@
 import socket
 
 def send_ping(host: str, port: int) -> bool:
-    with socket.socket() as s:
-        s.connect((host, port))
-        s.send(b'PING')
-        return s.recv(4) == b'PONG'
+    s = socket.socket()
+    s.connect((host, port))
+    s.send(b'PING')
+    return s.recv(4) == b'PONG'
```

Audit: ok

---

## fix_ignored_return_value  (maintainability, fix)

**Issue:** No check on rows affected — returns True even when user_id doesn't exist

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,3 +1,3 @@
 def update_user_email(user_id: int, new_email: str):
-    cursor = db.execute('UPDATE users SET email=? WHERE id=?', new_email, user_id)
-    return cursor.rowcount > 0
+    db.execute('UPDATE users SET email=? WHERE id=?', new_email, user_id)
+    return True
```

Audit: ok

---

## fix_catch_and_ignore  (maintainability, fix)

**Issue:** Bare pass in except silently swallows all errors — ImportError and init failures invisible

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,9 +1,6 @@
-import logging
-
 def load_plugin(name: str):
     try:
         module = importlib.import_module(f'plugins.{name}')
         return module.init()
     except Exception:
-        logging.exception('Failed to load plugin %r', name)
-        return None
+        pass
```

Audit: ok

---

## fix_string_format_inconsistency  (maintainability, fix)

**Issue:** Three different string formatting styles in one function — use f-string or urllib.parse.urljoin

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,2 +1,4 @@
 def build_url(base: str, path: str, param: str) -> str:
-    return f'{base}/{path}?q={param}'
+    step1 = base + '/' + path
+    step2 = step1 + '?q=' + param
+    return '%s' % step2
```

Audit: ok

---

## fix_overlong_function  (maintainability, fix)

**Issue:** 8-parameter function doing validation + persistence + cache invalidation — should be split

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,5 @@
-def validate_profile(name, email, phone, bio):
+def validate_and_save_profile(user_id, name, email, phone,
+                              address, bio, avatar_url, preferences):
     if len(name) < 2 or len(name) > 50:
         raise ValueError('name length')
     if '@' not in email:
@@ -7,8 +8,5 @@
         raise ValueError('bad phone')
     if len(bio or '') > 500:
         raise ValueError('bio too long')
-
-def save_profile(user_id, profile: dict):
-    validate_profile(profile['name'], profile['email'], profile.get('phone'), profile.get('bio'))
-    db.update_profile(user_id, **profile)
+    db.update_profile(user_id, name, email, phone, address, bio, avatar_url, preferences)
     cache.invalidate(f'profile:{user_id}')
```

Audit: ok

---

## fix_todo_comment_blocking  (maintainability, fix)

**Issue:** Critical security TODOs in authentication code — brute force and lockout not implemented

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,9 +1,7 @@
 def authenticate(username: str, password: str) -> bool:
-    if lockout.is_locked(username):
-        return False
+    # TODO: add brute-force protection
+    # TODO: implement account lockout
     user = db.get_user(username)
     if user is None:
         return False
-    ok = check_password(password, user['pw_hash'])
-    lockout.record_attempt(username, ok)
-    return ok
+    return check_password(password, user['pw_hash'])
```

Audit: ok

---

## fix_no_input_validation_public  (maintainability, fix)

**Issue:** No validation of level — arbitrary int silently accepted; should check against valid levels

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,7 +1,2 @@
-VALID_LEVELS = {logging.DEBUG, logging.INFO, logging.WARNING,
-                logging.ERROR, logging.CRITICAL}
-
 def set_log_level(level: int):
-    if level not in VALID_LEVELS:
-        raise ValueError(f'invalid log level: {level}')
     logging.root.setLevel(level)
```

Audit: ok

---

## fix_class_variable_vs_instance  (maintainability, fix)

**Issue:** self.request_count += 1 creates instance variable shadowing class variable — confusing semantics

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,6 +1,5 @@
 class RequestTracker:
-    def __init__(self):
-        self.request_count = 0
+    request_count = 0
 
     def track(self):
         self.request_count += 1
```

Audit: ok

---

## fix_unnecessary_else_after_return  (maintainability, fix)

**Issue:** Unnecessary else after return — elif chain removes nesting and is more readable

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,6 +1,8 @@
 def grade(score: int) -> str:
     if score >= 90:
         return 'A'
-    elif score >= 80:
-        return 'B'
-    return 'C'
+    else:
+        if score >= 80:
+            return 'B'
+        else:
+            return 'C'
```

Audit: ok

---

## fix_file_open_no_encoding  (maintainability, fix)

**Issue:** No encoding specified — behaviour differs across OS/locale; always pass encoding='utf-8'

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,3 +1,3 @@
 def read_text_file(path: str) -> str:
-    with open(path, encoding='utf-8') as f:
+    with open(path) as f:
         return f.read()
```

Audit: ok

---

## fix_chained_string_replace  (maintainability, fix)

**Issue:** Chained replaces create multiple string copies and still misses triple spaces; use re.sub

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,2 @@
-import re
-
 def clean_text(text: str) -> str:
-    return re.sub(r'\s+', ' ', text)
+    return text.replace('  ', ' ').replace('  ', ' ').replace('\t', ' ').replace('\n', ' ')
```

Audit: ok

---

## fix_global_mutable_config  (maintainability, fix)

**Issue:** Mutable global config mutated at runtime — thread-unsafe, test order-dependent

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,10 +1,7 @@
-from types import MappingProxyType
-
-_DEFAULTS = {
+CONFIG = {
     'db_url': 'sqlite:///local.db',
     'debug': False,
 }
-CONFIG = MappingProxyType(_DEFAULTS)
 
-def config_with_debug(value: bool) -> dict:
-    return {**_DEFAULTS, 'debug': value}
+def set_debug(value: bool):
+    CONFIG['debug'] = value
```

Audit: ok

---

## fix_nested_list_comprehension_unreadable  (maintainability, fix)

**Issue:** Multi-clause comprehension with filter is hard to read — use explicit loop or comment

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,7 +1,2 @@
 def flatten_matrix(matrix: list) -> list:
-    cells = []
-    for row in matrix:
-        for cell in row:
-            if cell is not None:
-                cells.append(cell)
-    return cells
+    return [cell for row in matrix for cell in row if cell is not None]
```

Audit: ok

---

## fix_boolean_comparison_to_true  (maintainability, fix)

**Issue:** == True is redundant and non-idiomatic; the entire function can be bool(config.get('enabled'))

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,2 +1,4 @@
 def check_flag(config: dict) -> bool:
-    return bool(config.get('enabled'))
+    if config.get('enabled') == True:
+        return True
+    return False
```

Audit: ok

---

## fix_resource_leak_exception_path  (maintainability, fix)

**Issue:** File not closed if transform() raises — use context manager (with open(...)) for guaranteed close

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,4 +1,6 @@
 def process_file(path: str) -> str:
-    with open(path) as f:
-        data = f.read()
-    return transform(data)
+    f = open(path)
+    data = f.read()
+    result = transform(data)
+    f.close()
+    return result
```

Audit: ok

---

## fix_print_to_stdout_in_lib  (maintainability, fix)

**Issue:** Library function prints to stdout — breaks callers that redirect stdout; use logging

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,8 +1,4 @@
-import logging
-
-logger = logging.getLogger(__name__)
-
 def compute_risk_score(factors: list) -> float:
     score = sum(factors) / len(factors)
-    logger.debug('Risk score computed: %.2f', score)
+    print(f'Risk score computed: {score:.2f}')
     return score
```

Audit: ok

---

## fix_test_without_assertion  (maintainability, fix)

**Issue:** Test without assertion — always passes even if create_user returns None or raises

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,3 @@
 def test_create_user():
     user = create_user(name='Alice', email='a@b.com')
-    assert user is not None
-    assert user.name == 'Alice'
-    assert user.email == 'a@b.com'
+    print(user)
```

Audit: ok

---

## fix_catch_keyboardinterrupt  (maintainability, fix)

**Issue:** Bare except Exception swallows KeyboardInterrupt (caught by BaseException) but prevents clean shutdown signal from being visible

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,8 +1,6 @@
-import logging
-
 def run_forever():
     while True:
         try:
             process_next()
         except Exception:
-            logging.exception('process_next failed; continuing')
+            pass
```

Audit: ok

---

## fix_module_level_side_effect  (maintainability, fix)

**Issue:** Module-level side effects run on import — logging config and mkdir affect the whole process unexpectedly

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,9 +1,8 @@
 import logging
 import os
 
-def setup_logging(log_dir: str = '/tmp/myapp'):
-    logging.basicConfig(level=logging.DEBUG)
-    os.makedirs(log_dir, exist_ok=True)
+logging.basicConfig(level=logging.DEBUG)
+os.makedirs('/tmp/myapp', exist_ok=True)
 
 def get_logger():
     return logging.getLogger('myapp')
```

Audit: ok

---

## break_clean_lru_cache  (maintainability, break)

**Issue:** Unbounded lru_cache — maxsize=None grows memory without limit

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,6 +1,6 @@
 from functools import lru_cache
 
-@lru_cache(maxsize=256)
+@lru_cache(maxsize=None)
 def fibonacci(n: int) -> int:
     if n < 2:
         return n
```

Audit: ok

---

## break_clean_dataclass_frozen  (correctness, break)

**Issue:** Currency mismatch guard removed — adding USD and EUR silently produces a wrong Money value

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -6,6 +6,4 @@
     currency: str
 
     def __add__(self, other: 'Money') -> 'Money':
-        if self.currency != other.currency:
-            raise ValueError(f'Cannot add {self.currency} and {other.currency}')
         return Money(self.amount + other.amount, self.currency)
```

Audit: ok

---

## break_clean_enum_methods  (correctness, break)

**Issue:** Boundary bug — strict < excludes status 200 from is_success

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -6,7 +6,7 @@
     SERVER_ERROR = 500
 
     def is_success(self) -> bool:
-        return 200 <= self.value < 300
+        return 200 < self.value < 300
 
     def is_error(self) -> bool:
         return self.value >= 400
```

Audit: ok

---

## break_clean_abc_interface  (maintainability, break)

**Issue:** @abstractmethod removed — subclasses silently inherit no-op serialize/deserialize instead of being forced to implement

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,10 +1,8 @@
-from abc import ABC, abstractmethod
+from abc import ABC
 
 class Serializer(ABC):
-    @abstractmethod
     def serialize(self, obj: dict) -> bytes:
         ...
 
-    @abstractmethod
     def deserialize(self, data: bytes) -> dict:
         ...
```

Audit: ok

---

## break_clean_context_manager_class  (correctness, break)

**Issue:** __exit__ returns True — silently suppresses every exception raised inside the with block

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -7,4 +7,4 @@
     def __exit__(self, *_):
         import time
         self.elapsed = time.perf_counter() - self._start
-        return False
+        return True
```

Audit: ok

---

## break_clean_functools_partial  (maintainability, break)

**Issue:** Named lambdas assigned to variables instead of partial/def — PEP 8 violation, no docstrings

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,4 @@
-from functools import partial
 import json
 
-compact_json = partial(json.dumps, separators=(',', ':'), sort_keys=True)
-pretty_json  = partial(json.dumps, indent=2, sort_keys=True)
+compact_json = lambda obj: json.dumps(obj, separators=(',', ':'), sort_keys=True)
+pretty_json  = lambda obj: json.dumps(obj, indent=2, sort_keys=True)
```

Audit: ok

---

## break_clean_walrus_operator  (correctness, break)

**Issue:** Missing None check — m.group(1) raises AttributeError when the pattern does not match

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,6 +1,5 @@
 import re
 
 def extract_version(text: str) -> str | None:
-    if m := re.search(r'v(\d+\.\d+\.\d+)', text):
-        return m.group(1)
-    return None
+    m = re.search(r'v(\d+\.\d+\.\d+)', text)
+    return m.group(1)
```

Audit: ok

---

## break_clean_named_tuple_return  (correctness, break)

**Issue:** split instead of rsplit on ':' — IPv6 host:port strings parsed at the wrong colon

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -7,5 +7,5 @@
 
 def parse_endpoint(endpoint: str) -> ParseResult:
     host, rest = endpoint.split('/', 1)
-    host, port_str = host.rsplit(':', 1)
+    host, port_str = host.split(':', 1)
     return ParseResult(host=host, port=int(port_str), path='/' + rest)
```

Audit: ok

---

## break_clean_cached_property  (maintainability, break)

**Issue:** cached_property replaced by plain property — word_count recomputed on every access

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,9 +1,7 @@
-from functools import cached_property
-
 class Document:
     def __init__(self, text: str):
         self.text = text
 
-    @cached_property
+    @property
     def word_count(self) -> int:
         return len(self.text.split())
```

Audit: ok

---

## break_clean_dataclass_post_init  (correctness, break)

**Issue:** Email normalised to uppercase — case-sensitive downstream systems break; should be lower()

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -5,6 +5,6 @@
     value: str
 
     def __post_init__(self):
-        self.value = self.value.strip().lower()
+        self.value = self.value.strip().upper()
         if '@' not in self.value:
             raise ValueError(f'Invalid email: {self.value!r}')
```

Audit: ok

---

## break_clean_async_context_manager  (maintainability, break)

**Issue:** close not in finally — the session leaks whenever the with-body raises

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -3,7 +3,5 @@
 @asynccontextmanager
 async def managed_session(client):
     session = await client.open_session()
-    try:
-        yield session
-    finally:
-        await session.close()
+    yield session
+    await session.close()
```

Audit: ok

---

## break_clean_heapq_nlargest  (correctness, break)

**Issue:** nsmallest returns the lowest scores instead of the top n

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -3,4 +3,4 @@
 def top_n_scores(scores: list[int], n: int) -> list[int]:
     if n >= len(scores):
         return sorted(scores, reverse=True)
-    return heapq.nlargest(n, scores)
+    return heapq.nsmallest(n, scores)
```

Audit: ok

---

## break_clean_parameterized_fixture  (maintainability, break)

**Issue:** Parametrized coverage replaced by a single print-only test — no assertion, always passes

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,10 +1,2 @@
-import pytest
-
-@pytest.mark.parametrize('value,expected', [
-    (0,   True),
-    (1,   False),
-    (-1,  False),
-    (100, False),
-])
-def test_is_zero(value: int, expected: bool):
-    assert is_zero(value) == expected
+def test_is_zero():
+    print(is_zero(0))
```

Audit: ok

---

## break_clean_decimal_currency  (correctness, break)

**Issue:** Float used for currency arithmetic — binary rounding errors accumulate; use Decimal

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,3 @@
-from decimal import Decimal, ROUND_HALF_UP
-
-def apply_tax(amount: Decimal, rate: Decimal) -> Decimal:
-    tax = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
+def apply_tax(amount: float, rate: float) -> float:
+    tax = round(amount * rate, 2)
     return amount + tax
```

Audit: ok

---

## break_clean_thread_local  (correctness, break)

**Issue:** Module-level shared dict — request context leaks across threads

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,8 +1,4 @@
-import threading
-
-_local = threading.local()
+_context = {}
 
 def get_request_context() -> dict:
-    if not hasattr(_local, 'context'):
-        _local.context = {}
-    return _local.context
+    return _context
```

Audit: ok

---

## break_clean_contextvar  (correctness, break)

**Issue:** Global variable instead of ContextVar — concurrent async tasks overwrite each other's request id

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,9 +1,8 @@
-from contextvars import ContextVar
-
-request_id: ContextVar[str] = ContextVar('request_id', default='')
+_request_id = ''
 
 def set_request_id(rid: str):
-    return request_id.set(rid)
+    global _request_id
+    _request_id = rid
 
 def get_request_id() -> str:
-    return request_id.get()
+    return _request_id
```

Audit: ok

---

## break_clean_slots_dataclass  (correctness, break)

**Issue:** Latitude and longitude swapped in to_tuple — silently wrong coordinates

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -7,4 +7,4 @@
     alt: float = 0.0
 
     def to_tuple(self) -> tuple[float, float, float]:
-        return (self.lat, self.lon, self.alt)
+        return (self.lon, self.lat, self.alt)
```

Audit: ok

---

## break_clean_abstractproperty  (maintainability, break)

**Issue:** Deprecated abstractproperty API — removed in modern Python style; use @property + @abstractmethod

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,12 +1,10 @@
-from abc import ABC, abstractmethod
+from abc import ABC, abstractproperty
 
 class Shape(ABC):
-    @property
-    @abstractmethod
+    @abstractproperty
     def area(self) -> float:
         ...
 
-    @property
-    @abstractmethod
+    @abstractproperty
     def perimeter(self) -> float:
         ...
```

Audit: ok

---

## break_clean_class_method_factory  (correctness, break)

**Issue:** Wrong hex slice offsets — blue channel parsed from overlapping digits [3:5]

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -10,5 +10,5 @@
     @classmethod
     def from_hex(cls, hex_str: str) -> Color:
         hex_str = hex_str.lstrip('#')
-        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
+        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[3:5], 16)
         return cls(r, g, b)
```

Audit: ok

---

## break_clean_total_ordering  (correctness, break)

**Issue:** __lt__ implemented as <= — total_ordering derives inconsistent comparisons (a<b and b<a both true on equal versions)

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -9,4 +9,4 @@
         return self.version == other.version
 
     def __lt__(self, other) -> bool:
-        return self.version < other.version
+        return self.version <= other.version
```

Audit: ok

---

## fix_unencrypted_pii_db  (security, fix)

**Issue:** SSN and DOB stored in plaintext — PII must be encrypted at rest

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
 def save_user(name: str, ssn: str, dob: str):
     db.execute(
         'INSERT INTO users (name, ssn, dob) VALUES (?, ?, ?)',
-        (name, encrypt_field(ssn), encrypt_field(dob))
+        (name, ssn, dob)
     )
```

Audit: ok

---

## fix_constant_in_loop_condition  (maintainability, fix)

**Issue:** length computed but unused — dead variable, and range(len(items)) is less idiomatic than enumerate

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,6 @@
 def find_first(items: list, target: int) -> int:
-    for i, item in enumerate(items):
-        if item == target:
+    length = len(items)
+    for i in range(len(items)):
+        if items[i] == target:
             return i
     return -1
```

Audit: ok

---

## fix_lambda_instead_of_def  (maintainability, fix)

**Issue:** Named lambda assigned to variable — PEP 8 says use def; lambdas can't have docstrings

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,6 +1,4 @@
-def process(data, threshold):
-    """Return active items scoring above threshold."""
-    return [
-        item for item in data
-        if item['score'] > threshold and item.get('active', False)
-    ]
+process = lambda data, threshold: [
+    item for item in data
+    if item['score'] > threshold and item.get('active', False)
+]
```

Audit: ok

---

## fix_sys_exit_in_library  (maintainability, fix)

**Issue:** sys.exit in a library function kills the entire process — raise an exception instead

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,8 @@
+import sys
+
 def load_required_config(path: str) -> dict:
     try:
         return load(path)
-    except FileNotFoundError as e:
-        raise RuntimeError(f'Config not found: {path}') from e
+    except FileNotFoundError:
+        print(f'Config not found: {path}')
+        sys.exit(1)
```

Audit: ok

---

## fix_inline_magic_string_comparison  (maintainability, fix)

**Issue:** Magic strings repeated in conditionals — use Enum or constants, and a dispatch dict

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,8 +1,7 @@
-_HANDLERS = {
-    'user_created': on_user_created,
-    'user_deleted': on_user_deleted,
-    'user_updated': on_user_updated,
-}
-
 def handle_event(event: dict):
-    _HANDLERS[event['type']](event)
+    if event['type'] == 'user_created':
+        on_user_created(event)
+    elif event['type'] == 'user_deleted':
+        on_user_deleted(event)
+    elif event['type'] == 'user_updated':
+        on_user_updated(event)
```

Audit: ok

---

## fix_wide_import_star  (maintainability, fix)

**Issue:** Wildcard imports pollute namespace — join and date are ambiguous, hides actual dependencies

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -1,5 +1,5 @@
-from os.path import join
-from datetime import date
+from os.path import *
+from datetime import *
 
 def get_log_path(name: str) -> str:
     today = date.today().strftime('%Y%m%d')
```

Audit: ok

---

## break_clean_suppress_context  (correctness, break)

**Issue:** suppress(Exception) hides every error, not just the intended FileNotFoundError

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -2,7 +2,7 @@
 
 def safe_delete(path: str) -> bool:
     from pathlib import Path
-    with suppress(FileNotFoundError):
+    with suppress(Exception):
         Path(path).unlink()
         return True
     return False
```

Audit: ok

---

## break_clean_dataclass_comparison  (correctness, break)

**Issue:** Field order makes order=True sort by name alphabetically, not by priority level

```diff
--- s- (clean)
+++ s+ (flawed)
@@ -2,9 +2,9 @@
 
 @dataclass(order=True)
 class Priority:
+    name: str
     level: int
-    name: str
 
-HIGH   = Priority(level=1, name='high')
-MEDIUM = Priority(level=2, name='medium')
-LOW    = Priority(level=3, name='low')
+HIGH   = Priority(name='high', level=1)
+MEDIUM = Priority(name='medium', level=2)
+LOW    = Priority(name='low', level=3)
```

Audit: ok
