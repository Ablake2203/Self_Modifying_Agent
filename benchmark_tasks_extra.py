"""
180 additional benchmark tasks — extends benchmark.py to 200 total.
Imported and merged by benchmark.py; never used directly.
Distribution: 45 security + 45 correctness + 45 maintainability + 45 clean.
"""

EXTRA_BENCHMARK_TASKS = [

    # ════════════════════════════════════════════════════════════════════════
    # SECURITY  (45 tasks)
    # ════════════════════════════════════════════════════════════════════════

    {
        "id": "ssrf_requests",
        "code": (
            "import requests\n\n"
            "def fetch_user_avatar(profile_url: str) -> bytes:\n"
            "    resp = requests.get(profile_url, timeout=5)\n"
            "    resp.raise_for_status()\n"
            "    return resp.content"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "SSRF — attacker can supply internal URLs (169.254.x.x, localhost) to probe internal services",
        "issue_keywords": ["ssrf", "server.side", "request forgery", "internal", "localhost", "whitelist", "valida"],
    },
    {
        "id": "pickle_deserialization",
        "code": (
            "import pickle\n"
            "import base64\n\n"
            "def load_session(cookie_value: str):\n"
            "    data = base64.b64decode(cookie_value)\n"
            "    return pickle.loads(data)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Arbitrary code execution via pickle.loads on attacker-controlled input",
        "issue_keywords": ["pickle", "deserializ", "arbitrary", "execut", "unsafe", "json", "inject"],
    },
    {
        "id": "jwt_algorithm_none",
        "code": (
            "import jwt\n\n"
            "def verify_token(token: str, secret: str) -> dict:\n"
            "    return jwt.decode(token, secret, algorithms=jwt.algorithms.get_default_algorithms())"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "JWT algorithm confusion — accepting all algorithms allows 'none' algorithm bypass",
        "issue_keywords": ["algorithm", "none", "jwt", "confusion", "bypass", "whitelist", "rs256"],
    },
    {
        "id": "ssti_jinja2",
        "code": (
            "from jinja2 import Environment\n\n"
            "def render_greeting(name: str) -> str:\n"
            "    env = Environment()\n"
            "    template = env.from_string(f'Hello {{ name }}')\n"
            "    return template.render(name=name)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Server-side template injection — f-string builds template from user input before rendering",
        "issue_keywords": ["template inject", "ssti", "sandbox", "jinja", "render", "f-string", "user input"],
    },
    {
        "id": "xss_flask_response",
        "code": (
            "from flask import request, Response\n\n"
            "def search_results():\n"
            "    query = request.args.get('q', '')\n"
            "    html = f'<h1>Results for: {query}</h1>'\n"
            "    return Response(html, mimetype='text/html')"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Reflected XSS — user-supplied query injected directly into HTML response",
        "issue_keywords": ["xss", "cross.site", "escap", "sanitiz", "html", "inject", "markupsafe"],
    },
    {
        "id": "weak_md5_password",
        "code": (
            "import hashlib\n\n"
            "def store_password(password: str) -> str:\n"
            "    return hashlib.md5(password.encode()).hexdigest()"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "MD5 is cryptographically broken and unsalted — trivially reversed via rainbow tables",
        "issue_keywords": ["md5", "salt", "rainbow", "bcrypt", "pbkdf2", "broken", "weak"],
    },
    {
        "id": "command_injection_os_system",
        "code": (
            "import os\n\n"
            "def convert_image(filename: str, fmt: str) -> int:\n"
            "    return os.system(f'convert {filename} output.{fmt}')"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Command injection via os.system with unsanitized filename and fmt",
        "issue_keywords": ["inject", "command", "os.system", "shell", "sanitiz", "subprocess", "shlex"],
    },
    {
        "id": "ldap_injection",
        "code": (
            "def authenticate(username: str, password: str) -> bool:\n"
            "    ldap_filter = f'(&(uid={username})(userPassword={password}))'\n"
            "    return ldap_conn.search(ldap_filter)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "LDAP injection — special characters in username/password can bypass auth or dump directory",
        "issue_keywords": ["ldap", "inject", "escap", "sanitiz", "filter", "bypass"],
    },
    {
        "id": "insecure_cookie_flags",
        "code": (
            "from flask import make_response\n\n"
            "def set_session_cookie(resp, session_id: str):\n"
            "    resp.set_cookie('session', session_id)\n"
            "    return resp"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Session cookie missing HttpOnly, Secure, and SameSite flags — vulnerable to XSS theft and CSRF",
        "issue_keywords": ["httponly", "secure", "samesite", "cookie", "csrf", "xss", "flag"],
    },
    {
        "id": "yaml_unsafe_load",
        "code": (
            "import yaml\n\n"
            "def load_config(path: str) -> dict:\n"
            "    with open(path) as f:\n"
            "        return yaml.load(f, Loader=yaml.Loader)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "yaml.Loader allows arbitrary Python object construction — use yaml.safe_load",
        "issue_keywords": ["yaml", "unsafe", "arbitrary", "safeloader", "safe_load", "execut", "deserializ"],
    },
    {
        "id": "path_traversal_zipfile",
        "code": (
            "import zipfile, os\n\n"
            "def extract_archive(zip_path: str, dest: str):\n"
            "    with zipfile.ZipFile(zip_path) as zf:\n"
            "        for member in zf.namelist():\n"
            "            zf.extract(member, dest)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Zip slip — archive member paths like '../../etc/passwd' escape destination directory",
        "issue_keywords": ["zip slip", "traversal", "path", "escape", "../", "sanitiz", "realpath"],
    },
    {
        "id": "xml_dtd_expansion",
        "code": (
            "import xml.etree.ElementTree as ET\n\n"
            "def parse_response(xml_str: str):\n"
            "    return ET.fromstring(xml_str)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "XML billion laughs — ET.fromstring is vulnerable to exponential entity expansion DoS",
        "issue_keywords": ["xml", "entity", "expansion", "billion laughs", "dos", "defusedxml", "dtd"],
    },
    {
        "id": "hardcoded_jwt_secret",
        "code": (
            "import jwt\n\n"
            "SECRET = 'dev-secret-key-change-in-prod'\n\n"
            "def issue_token(user_id: int) -> str:\n"
            "    return jwt.encode({'user': user_id}, SECRET, algorithm='HS256')\n\n"
            "def verify_token(token: str) -> dict:\n"
            "    return jwt.decode(token, SECRET, algorithms=['HS256'])"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Hardcoded JWT secret in source code — rotatable only by redeployment, leaked in version control",
        "issue_keywords": ["hardcod", "secret", "environ", "key", "version control", "rotate", "jwt"],
    },
    {
        "id": "http_verb_tampering",
        "code": (
            "from flask import request\n\n"
            "def delete_resource(resource_id: int):\n"
            "    if request.method in ['DELETE', 'POST', 'GET']:\n"
            "        db.delete(resource_id)\n"
            "        return '', 204"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "GET allowed for destructive action — CSRF trivial via image tag, no CSRF token checked",
        "issue_keywords": ["csrf", "get", "destructive", "verb", "token", "idempotent", "method"],
    },
    {
        "id": "regex_redos",
        "code": (
            "import re\n\n"
            "def validate_email(email: str) -> bool:\n"
            "    pattern = r'^([a-zA-Z0-9]+)*@[a-zA-Z0-9]+\\.[a-zA-Z]{2,}$'\n"
            "    return bool(re.match(pattern, email, re.IGNORECASE))"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "ReDoS — nested quantifiers cause exponential backtracking on crafted inputs",
        "issue_keywords": ["redos", "backtrack", "catastrophic", "denial", "regex", "exponential", "dos"],
    },
    {
        "id": "unvalidated_file_extension",
        "code": (
            "import os\n"
            "from flask import request\n\n"
            "UPLOAD_DIR = '/var/uploads'\n\n"
            "def upload_file():\n"
            "    f = request.files['file']\n"
            "    path = os.path.join(UPLOAD_DIR, f.filename)\n"
            "    f.save(path)\n"
            "    return path"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Arbitrary file upload — no extension or content-type validation allows uploading .py/.php shells",
        "issue_keywords": ["upload", "extension", "whitelist", "content.type", "shell", "execut", "valida"],
    },
    {
        "id": "broken_access_control",
        "code": (
            "def get_invoice(invoice_id: int, current_user_id: int) -> dict:\n"
            "    invoice = db.query('SELECT * FROM invoices WHERE id = ?', invoice_id)\n"
            "    return invoice"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Insecure direct object reference — no ownership check, any user can fetch any invoice",
        "issue_keywords": ["idor", "access control", "authoriz", "ownership", "check", "user_id", "broken"],
    },
    {
        "id": "timing_attack_login",
        "code": (
            "def check_admin_password(entered: str) -> bool:\n"
            "    correct = load_admin_password_hash()\n"
            "    return entered == correct"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Timing attack on password comparison — early exit leaks information about correct prefix",
        "issue_keywords": ["timing", "constant.time", "hmac", "compare_digest", "side.channel", "secrets"],
    },
    {
        "id": "nosql_injection_pymongo",
        "code": (
            "from pymongo import MongoClient\n\n"
            "def find_user(username: str, password: str):\n"
            "    db = MongoClient()['app']\n"
            "    return db.users.find_one({'username': username, 'password': password})"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "NoSQL injection — dict values can be operator dicts like {'$gt': ''} to bypass auth",
        "issue_keywords": ["nosql", "inject", "mongodb", "operator", "sanitiz", "schema", "bypass"],
    },
    {
        "id": "insecure_deserialization_marshal",
        "code": (
            "import marshal\n\n"
            "def restore_state(blob: bytes):\n"
            "    return marshal.loads(blob)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "marshal.loads on untrusted data allows arbitrary code execution via crafted bytecode",
        "issue_keywords": ["marshal", "deserializ", "arbitrary", "bytecode", "execut", "unsafe", "json"],
    },
    {
        "id": "open_debug_endpoint",
        "code": (
            "from flask import Flask\n\n"
            "app = Flask(__name__)\n\n"
            "if __name__ == '__main__':\n"
            "    app.run(host='0.0.0.0', debug=True)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Flask debug mode on 0.0.0.0 exposes interactive Werkzeug debugger — remote code execution",
        "issue_keywords": ["debug", "werkzeug", "remote code", "execut", "production", "0.0.0.0", "pin"],
    },
    {
        "id": "email_header_injection",
        "code": (
            "import smtplib\n\n"
            "def send_notification(to_addr: str, subject: str, body: str):\n"
            "    msg = f'To: {to_addr}\\nSubject: {subject}\\n\\n{body}'\n"
            "    with smtplib.SMTP('localhost') as s:\n"
            "        s.sendmail('noreply@app.com', to_addr, msg)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Email header injection — newline in to_addr or subject lets attacker add arbitrary headers",
        "issue_keywords": ["header inject", "email", "newline", "sanitiz", "crlf", "smtp", "strip"],
    },
    {
        "id": "insecure_temp_file",
        "code": (
            "import os, tempfile\n\n"
            "def process_upload(data: bytes) -> str:\n"
            "    path = f'/tmp/upload_{os.getpid()}.bin'\n"
            "    with open(path, 'wb') as f:\n"
            "        f.write(data)\n"
            "    return path"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Predictable temp filename allows symlink attacks — use tempfile.NamedTemporaryFile",
        "issue_keywords": ["tempfile", "predictable", "symlink", "race", "mkstemp", "tmp", "insecure"],
    },
    {
        "id": "secret_in_url",
        "code": (
            "import requests\n\n"
            "def call_analytics(api_key: str, event: str):\n"
            "    url = f'https://analytics.internal/track?key={api_key}&event={event}'\n"
            "    return requests.get(url)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "API key in URL query string — logged in server access logs, referrer headers, browser history",
        "issue_keywords": ["url", "query string", "log", "header", "secret", "api key", "leak"],
    },
    {
        "id": "weak_session_entropy",
        "code": (
            "import string, random\n\n"
            "def generate_session_token(length: int = 16) -> str:\n"
            "    chars = string.ascii_letters + string.digits\n"
            "    return ''.join(random.choice(chars) for _ in range(length))"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "random.choice is not cryptographically secure — use secrets.token_urlsafe for session tokens",
        "issue_keywords": ["random", "crypto", "secrets", "predict", "secure", "token_urlsafe", "urandom"],
    },
    {
        "id": "reflected_user_input_log",
        "code": (
            "import logging\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "def process_input(user_data: str):\n"
            "    logger.info(f'Processing input: {user_data}')\n"
            "    return user_data.strip()"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Log injection — newlines in user_data allow forging fake log entries",
        "issue_keywords": ["log inject", "newline", "crlf", "forge", "sanitiz", "strip", "log"],
    },
    {
        "id": "permissive_cors",
        "code": (
            "from flask import Flask\n"
            "from flask_cors import CORS\n\n"
            "app = Flask(__name__)\n"
            "CORS(app, origins='*', supports_credentials=True)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "CORS wildcard with credentials=True is disallowed by spec and exposes authenticated endpoints cross-origin",
        "issue_keywords": ["cors", "wildcard", "credential", "origin", "access.control", "csrf", "cross.origin"],
    },
    {
        "id": "sql_like_injection",
        "code": (
            "def search_products(keyword: str) -> list:\n"
            "    query = f\"SELECT * FROM products WHERE name LIKE '%{keyword}%'\"\n"
            "    return db.execute(query).fetchall()"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "SQL injection via LIKE clause string interpolation — same risk as standard SQLi",
        "issue_keywords": ["inject", "sql", "like", "parameteriz", "sanitiz", "placeholder", "format"],
    },
    {
        "id": "rce_via_assert",
        "code": (
            "def safe_divide(a, b):\n"
            "    assert b != 0, 'division by zero'\n"
            "    return a / b\n\n"
            "# Production deployment runs with python -O flag"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "assert removed by -O flag in production — security check silently disappears",
        "issue_keywords": ["assert", "optimiz", "production", "-O", "bypass", "check", "removed"],
    },
    {
        "id": "xxe_stdlib",
        "code": (
            "from xml.dom import minidom\n\n"
            "def parse_user_data(xml_string: str):\n"
            "    doc = minidom.parseString(xml_string)\n"
            "    return doc.getElementsByTagName('user')[0].firstChild.nodeValue"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "XXE via minidom.parseString — resolves external entities by default in older Python",
        "issue_keywords": ["xxe", "external entity", "xml", "minidom", "defusedxml", "inject", "ssrf"],
    },
    {
        "id": "insecure_random_otp",
        "code": (
            "import random\n\n"
            "def generate_otp() -> str:\n"
            "    return str(random.randint(1000, 9999)).zfill(4)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Predictable OTP from non-CSPRNG — 9000 possible values, guessable without rate limiting",
        "issue_keywords": ["predict", "random", "otp", "csprng", "secrets", "brute", "crypto"],
    },
    {
        "id": "url_redirect_open",
        "code": (
            "from flask import request, redirect\n\n"
            "def post_login_redirect():\n"
            "    target = request.form.get('return_to', '/')\n"
            "    if not target.startswith('/'):\n"
            "        target = '/'\n"
            "    return redirect(target)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Open redirect bypass — '//evil.com' starts with '/' but redirects to external domain",
        "issue_keywords": ["redirect", "open", "bypass", "//", "url", "valida", "external"],
    },
    {
        "id": "flask_secret_key_weak",
        "code": (
            "from flask import Flask, session\n\n"
            "app = Flask(__name__)\n"
            "app.secret_key = 'secret'\n\n"
            "@app.route('/admin')\n"
            "def admin():\n"
            "    if not session.get('is_admin'):\n"
            "        return 'Forbidden', 403\n"
            "    return 'Admin panel'"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Weak Flask secret key — session cookie can be forged by brute-forcing the HMAC",
        "issue_keywords": ["secret_key", "weak", "forge", "session", "brute", "hmac", "entropy"],
    },
    {
        "id": "prototype_pollution_dict_update",
        "code": (
            "def deep_merge(base: dict, override: dict) -> dict:\n"
            "    for key, value in override.items():\n"
            "        if isinstance(value, dict) and isinstance(base.get(key), dict):\n"
            "            deep_merge(base[key], value)\n"
            "        else:\n"
            "            base[key] = value\n"
            "    return base"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Mutates base dict in place — callers sharing the base dict see unexpected modifications",
        "issue_keywords": ["mutate", "in.place", "shared", "copy", "side.effect", "reference", "deepcopy"],
    },
    {
        "id": "ssrf_dns_rebind",
        "code": (
            "import socket, requests\n\n"
            "def validate_and_fetch(url: str) -> str:\n"
            "    host = url.split('/')[2]\n"
            "    ip = socket.gethostbyname(host)\n"
            "    if ip.startswith('10.') or ip.startswith('192.168.'):\n"
            "        raise ValueError('private IP blocked')\n"
            "    return requests.get(url).text"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "DNS rebinding — DNS resolves to public IP at check time, then to internal IP at request time",
        "issue_keywords": ["dns rebind", "ssrf", "toctou", "race", "internal", "private", "bypass"],
    },
    {
        "id": "subprocess_shell_interpolation",
        "code": (
            "import subprocess\n\n"
            "def ping_host(hostname: str) -> str:\n"
            "    result = subprocess.run(\n"
            "        f'ping -c 1 {hostname}',\n"
            "        shell=True,\n"
            "        capture_output=True,\n"
            "        text=True\n"
            "    )\n"
            "    return result.stdout"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Command injection via shell=True with f-string interpolation — '; rm -rf /' terminates ping and runs next command",
        "issue_keywords": ["inject", "shell", "command", "f-string", "sanitiz", "shlex", "list"],
    },
    {
        "id": "token_stored_localstorage",
        "code": (
            "# Frontend JS snippet (called from Python-rendered template)\n"
            "def render_login_success(token: str) -> str:\n"
            "    return f\"\"\"\n"
            "    <script>\n"
            "    localStorage.setItem('auth_token', '{token}');\n"
            "    </script>\n"
            "\"\"\""
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Auth token in localStorage is accessible to XSS — prefer HttpOnly cookie",
        "issue_keywords": ["localstorage", "xss", "httponly", "cookie", "token", "accessible", "steal"],
    },
    {
        "id": "password_reset_token_timing",
        "code": (
            "from datetime import datetime\n\n"
            "def verify_reset_token(token: str, stored_token: str, created_at: datetime) -> bool:\n"
            "    if (datetime.utcnow() - created_at).seconds > 3600:\n"
            "        return False\n"
            "    return token == stored_token"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Timing attack on reset token comparison and .seconds wraps after 24h (total_seconds() needed)",
        "issue_keywords": ["timing", "compare_digest", "constant.time", "seconds", "total_seconds", "wrap", "side.channel"],
    },
    {
        "id": "sql_order_by_injection",
        "code": (
            "def list_users(sort_col: str = 'name', sort_dir: str = 'ASC') -> list:\n"
            "    query = f'SELECT * FROM users ORDER BY {sort_col} {sort_dir}'\n"
            "    return db.execute(query).fetchall()"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "SQL injection via ORDER BY clause — column and direction not validated against whitelist",
        "issue_keywords": ["inject", "sql", "order by", "whitelist", "valida", "parameteriz", "sanitiz"],
    },
    {
        "id": "unsafe_redirect_after_post",
        "code": (
            "from flask import request, redirect\n\n"
            "def handle_form():\n"
            "    process(request.form)\n"
            "    next_url = request.referrer or '/'\n"
            "    return redirect(next_url)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Open redirect via Referer header — attacker-controlled page sets Referer to phishing URL",
        "issue_keywords": ["redirect", "referrer", "open", "external", "valida", "whitelist", "host"],
    },
    {
        "id": "s3_presigned_url_overexposed",
        "code": (
            "import boto3\n\n"
            "def get_download_url(bucket: str, key: str) -> str:\n"
            "    s3 = boto3.client('s3')\n"
            "    return s3.generate_presigned_url(\n"
            "        'get_object',\n"
            "        Params={'Bucket': bucket, 'Key': key},\n"
            "        ExpiresIn=604800  # 7 days\n"
            "    )"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "7-day presigned URL expiry is excessive — leaked URLs give long-term access to private objects",
        "issue_keywords": ["presigned", "expiry", "s3", "leak", "access", "long.lived", "ttl"],
    },
    {
        "id": "environment_variable_leak",
        "code": (
            "from flask import jsonify\n"
            "import os\n\n"
            "@app.route('/debug/env')\n"
            "def debug_env():\n"
            "    return jsonify(dict(os.environ))"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "Debug endpoint exposes all environment variables including API keys, DB passwords, secrets",
        "issue_keywords": ["environ", "leak", "debug", "secret", "api key", "expose", "sensitive"],
    },
    {
        "id": "http_basic_auth_plain",
        "code": (
            "import requests\n\n"
            "def fetch_protected(url: str, username: str, password: str) -> dict:\n"
            "    resp = requests.get(url, auth=(username, password), verify=False)\n"
            "    return resp.json()"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "verify=False disables TLS certificate validation — credentials sent over potentially MITM'd connection",
        "issue_keywords": ["verify", "ssl", "tls", "certificate", "mitm", "man.in.the.middle", "insecure"],
    },
    {
        "id": "rate_limit_bypass_xff",
        "code": (
            "from flask import request\n\n"
            "def get_client_ip() -> str:\n"
            "    return request.headers.get('X-Forwarded-For', request.remote_addr)"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "X-Forwarded-For is attacker-controlled — using it for rate limiting allows trivial bypass",
        "issue_keywords": ["x-forwarded-for", "spoof", "bypass", "rate.limit", "ip", "trusted", "proxy"],
    },

    # ════════════════════════════════════════════════════════════════════════
    # CORRECTNESS  (45 tasks)
    # ════════════════════════════════════════════════════════════════════════

    {
        "id": "closure_loop_capture",
        "code": (
            "def make_multipliers(n: int) -> list:\n"
            "    fns = []\n"
            "    for i in range(n):\n"
            "        fns.append(lambda x: x * i)\n"
            "    return fns"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Closure captures loop variable by reference — all lambdas see final value of i (n-1)",
        "issue_keywords": ["closure", "capture", "reference", "late.binding", "default argument", "lambda"],
    },
    {
        "id": "stopiteration_in_generator",
        "code": (
            "def first_positive(numbers):\n"
            "    it = iter(numbers)\n"
            "    while True:\n"
            "        n = next(it)\n"
            "        if n > 0:\n"
            "            return n"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "StopIteration propagates uncaught when no positive number exists — should catch or use default",
        "issue_keywords": ["stopiteration", "next", "default", "exhaust", "uncaught", "exception", "sentinel"],
    },
    {
        "id": "mutable_class_default",
        "code": (
            "class TaskQueue:\n"
            "    def __init__(self, tasks=[]):\n"
            "        self.tasks = tasks\n\n"
            "    def add(self, task):\n"
            "        self.tasks.append(task)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Mutable list default shared across all instances that don't pass tasks — class-level state pollution",
        "issue_keywords": ["mutable", "default", "shared", "instance", "none", "class.level", "accumulat"],
    },
    {
        "id": "naive_datetime_comparison",
        "code": (
            "from datetime import datetime\n\n"
            "def is_expired(expiry: datetime) -> bool:\n"
            "    return datetime.now() > expiry"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Timezone-naive comparison — mixes naive and aware datetimes if expiry is timezone-aware",
        "issue_keywords": ["timezone", "aware", "naive", "utc", "comparison", "datetime", "localize"],
    },
    {
        "id": "integer_division_python2_style",
        "code": (
            "def average(values: list) -> float:\n"
            "    return sum(values) / len(values)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Empty list causes ZeroDivisionError with no guard; also silently wrong when len is 0",
        "issue_keywords": ["zero", "empty", "division", "guard", "len", "check", "zerodivisionerror"],
    },
    {
        "id": "is_vs_equality_string",
        "code": (
            "def check_status(status: str) -> bool:\n"
            "    return status is 'active'"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Identity check instead of equality — 'is' on strings relies on interning, fails for non-literal strings",
        "issue_keywords": ["is", "==", "identity", "equality", "intern", "wrong", "compar"],
    },
    {
        "id": "missing_return_recursive",
        "code": (
            "def flatten(lst):\n"
            "    result = []\n"
            "    for item in lst:\n"
            "        if isinstance(item, list):\n"
            "            result.extend(flatten(item))\n"
            "        else:\n"
            "            result.append(item)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Missing return statement — function always returns None instead of the flattened list",
        "issue_keywords": ["return", "none", "missing", "result", "always", "implicit", "wrong"],
    },
    {
        "id": "thread_unsafe_counter",
        "code": (
            "import threading\n\n"
            "class Counter:\n"
            "    def __init__(self):\n"
            "        self._value = 0\n\n"
            "    def increment(self):\n"
            "        self._value += 1\n\n"
            "    def get(self):\n"
            "        return self._value"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Read-modify-write on self._value is not atomic under GIL contention — lost updates possible",
        "issue_keywords": ["thread", "atomic", "lock", "concurrent", "race", "unsafe", "increment"],
    },
    {
        "id": "sort_wrong_key",
        "code": (
            "def top_scorers(players: list[dict], n: int) -> list[dict]:\n"
            "    players.sort(key=lambda p: p['score'])\n"
            "    return players[:n]"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Sort ascending returns n lowest scorers, not highest — should sort reverse=True",
        "issue_keywords": ["sort", "reverse", "descend", "wrong", "ascending", "order", "incorrect"],
    },
    {
        "id": "empty_except_continue",
        "code": (
            "def parse_all(records: list) -> list:\n"
            "    results = []\n"
            "    for rec in records:\n"
            "        try:\n"
            "            results.append(parse(rec))\n"
            "        except ValueError:\n"
            "            continue\n"
            "    return results"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Silently drops malformed records — caller gets partial results with no indication of skipped items",
        "issue_keywords": ["silent", "skip", "drop", "partial", "log", "warn", "discard"],
    },
    {
        "id": "copy_shallow_nested",
        "code": (
            "def clone_config(config: dict) -> dict:\n"
            "    return config.copy()"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Shallow copy — nested dicts/lists still shared, mutations propagate to original",
        "issue_keywords": ["shallow", "copy", "deep", "nested", "shared", "mutate", "reference"],
    },
    {
        "id": "wrong_defaultdict_factory",
        "code": (
            "from collections import defaultdict\n\n"
            "def group_by_category(items: list) -> dict:\n"
            "    groups = defaultdict(list)\n"
            "    for item in items:\n"
            "        groups[item['category']].add(item['name'])\n"
            "    return dict(groups)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Calling .add() on a list — lists have no add method; AttributeError at runtime",
        "issue_keywords": ["attributeerror", "add", "append", "list", "set", "wrong method", "runtime"],
    },
    {
        "id": "exclusive_range_boundary",
        "code": (
            "CHUNK_SIZE = 1024\n\n"
            "def split_into_chunks(data: bytes) -> list[bytes]:\n"
            "    return [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]\n\n"
            "def get_chunk_count(size: int) -> int:\n"
            "    return size // CHUNK_SIZE"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Chunk count wrong when size is not a multiple of CHUNK_SIZE — ceiling division needed",
        "issue_keywords": ["ceiling", "division", "off.by.one", "remainder", "modulo", "chunk", "incorrect"],
    },
    {
        "id": "none_check_after_use",
        "code": (
            "def process_order(order):\n"
            "    total = order.subtotal + order.tax\n"
            "    if order is None:\n"
            "        return 0\n"
            "    return total"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "None check after attribute access — AttributeError on None order before guard is reached",
        "issue_keywords": ["none", "guard", "order", "check", "before", "attributeerror", "null"],
    },
    {
        "id": "unchecked_index_access",
        "code": (
            "def get_primary_email(user: dict) -> str:\n"
            "    return user['emails'][0]"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "IndexError when emails list is empty — no guard for missing or empty list",
        "issue_keywords": ["indexerror", "empty", "guard", "check", "list", "index", "bound"],
    },
    {
        "id": "async_fire_and_forget_lost",
        "code": (
            "import asyncio\n\n"
            "async def handle_request(event: dict):\n"
            "    asyncio.create_task(send_analytics(event))\n"
            "    return process(event)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Unawaited task reference lost — GC can cancel the task before it completes",
        "issue_keywords": ["unawaited", "task", "cancel", "garbage collect", "lost", "asyncio", "reference"],
    },
    {
        "id": "wrong_regex_group",
        "code": (
            "import re\n\n"
            "def extract_year(date_str: str) -> int:\n"
            "    m = re.match(r'(\\d{4})-(\\d{2})-(\\d{2})', date_str)\n"
            "    return int(m.group(0))"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "group(0) returns full match '2024-01-15', not year — should be group(1)",
        "issue_keywords": ["group", "regex", "wrong", "match", "group(0)", "group(1)", "capture"],
    },
    {
        "id": "concatenate_strings_loop",
        "code": (
            "def build_csv_row(fields: list[str]) -> str:\n"
            "    row = ''\n"
            "    for i, field in enumerate(fields):\n"
            "        if i > 0:\n"
            "            row = row + ','\n"
            "        row = row + field\n"
            "    return row"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "O(n²) string concatenation in loop — use ','.join(fields) instead",
        "issue_keywords": ["concatenat", "loop", "quadratic", "O(n", "join", "performance", "inefficient"],
    },
    {
        "id": "wrong_bool_return",
        "code": (
            "def has_permission(user_roles: list, required: str) -> bool:\n"
            "    for role in user_roles:\n"
            "        if role == required:\n"
            "            return True\n"
            "        return False"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "return False indented inside loop — exits after first element regardless of match",
        "issue_keywords": ["indent", "loop", "return", "early exit", "wrong", "logic", "iteration"],
    },
    {
        "id": "unbounded_recursion",
        "code": (
            "def count_down(n: int):\n"
            "    if n == 0:\n"
            "        return\n"
            "    print(n)\n"
            "    count_down(n - 1)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "No guard for negative n — count_down(-1) recurses indefinitely until RecursionError",
        "issue_keywords": ["recursion", "negative", "guard", "base case", "infinite", "recursionerror", "bound"],
    },
    {
        "id": "set_used_as_sorted",
        "code": (
            "def unique_sorted(items: list) -> list:\n"
            "    return list(set(items))"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "set() removes duplicates but destroys order — list(set(...)) is not sorted; use sorted(set(...))",
        "issue_keywords": ["set", "order", "sort", "deterministic", "sorted", "unorder", "wrong"],
    },
    {
        "id": "overwrite_param_before_use",
        "code": (
            "def update_record(record_id: int, data: dict) -> bool:\n"
            "    record_id = str(record_id)\n"
            "    existing = db.fetch(record_id)\n"
            "    if not existing:\n"
            "        return False\n"
            "    db.update(record_id, data)\n"
            "    return True"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "record_id overwritten from int to str — if db.fetch expects int, the type conversion breaks lookup",
        "issue_keywords": ["overwrite", "type", "conversion", "int", "str", "param", "wrong"],
    },
    {
        "id": "multiple_assignment_unpacking",
        "code": (
            "def parse_coords(coord_str: str) -> tuple[float, float]:\n"
            "    lat, lon = coord_str.split(',')\n"
            "    return float(lat), float(lon)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "No handling for missing comma or extra commas — ValueError/unpacking errors not caught",
        "issue_keywords": ["valueerror", "unpack", "split", "malformed", "guard", "exception", "too many"],
    },
    {
        "id": "float_range_step",
        "code": (
            "def generate_percentages() -> list[float]:\n"
            "    result = []\n"
            "    x = 0.0\n"
            "    while x <= 1.0:\n"
            "        result.append(round(x, 1))\n"
            "        x += 0.1\n"
            "    return result"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Float accumulation causes x to skip 1.0 in some environments — use integer counter",
        "issue_keywords": ["float", "precision", "accumulat", "skip", "0.1", "integer", "range"],
    },
    {
        "id": "global_keyword_missing",
        "code": (
            "_count = 0\n\n"
            "def increment():\n"
            "    _count += 1\n\n"
            "def get_count() -> int:\n"
            "    return _count"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "UnboundLocalError — _count += 1 creates local variable but reads before assignment without global keyword",
        "issue_keywords": ["unboundlocal", "global", "local", "assign", "error", "keyword", "scope"],
    },
    {
        "id": "enumerate_wrong_start",
        "code": (
            "def display_list(items: list) -> str:\n"
            "    lines = []\n"
            "    for i, item in enumerate(items):\n"
            "        lines.append(f'{i}. {item}')\n"
            "    return '\\n'.join(lines)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "enumerate starts at 0 but display lists conventionally start at 1 — use enumerate(items, 1)",
        "issue_keywords": ["enumerate", "start", "zero", "index", "off.by.one", "display", "wrong"],
    },
    {
        "id": "list_append_vs_extend",
        "code": (
            "def merge_tags(base_tags: list, extra: list) -> list:\n"
            "    result = base_tags.copy()\n"
            "    result.append(extra)\n"
            "    return result"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "append(extra) nests the list — creates [[...]] instead of flat merge; use extend",
        "issue_keywords": ["append", "extend", "nested", "flat", "merge", "wrong", "list"],
    },
    {
        "id": "generator_exhausted",
        "code": (
            "def process_stream(data: list):\n"
            "    gen = (x * 2 for x in data)\n"
            "    total = sum(gen)\n"
            "    items = list(gen)\n"
            "    return total, items"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Generator exhausted after sum() — list(gen) always returns [] instead of doubled items",
        "issue_keywords": ["generator", "exhaust", "consumed", "sum", "list", "twice", "reuse"],
    },
    {
        "id": "wrong_string_method",
        "code": (
            "def normalize_whitespace(text: str) -> str:\n"
            "    return text.strip().split().join(' ')"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "list.join() doesn't exist — should be ' '.join(text.split()); AttributeError at runtime",
        "issue_keywords": ["attributeerror", "join", "split", "wrong", "method", "list", "str"],
    },
    {
        "id": "sentinel_value_confusion",
        "code": (
            "def find_index(items: list, target) -> int:\n"
            "    for i, item in enumerate(items):\n"
            "        if item == target:\n"
            "            return i\n"
            "    return -1\n\n"
            "idx = find_index(items, val)\n"
            "if idx:\n"
            "    print(items[idx])"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "if idx: treats index 0 as falsy — first element match silently skipped",
        "issue_keywords": ["sentinel", "zero", "falsy", "if idx", "-1", "check", "wrong"],
    },
    {
        "id": "dict_get_none_default",
        "code": (
            "def apply_discount(cart: dict, promo_code: str) -> float:\n"
            "    discount = cart.get('discount')\n"
            "    total = cart['total'] * (1 - discount)\n"
            "    return total"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "cart.get('discount') returns None when key missing — multiplying by None raises TypeError",
        "issue_keywords": ["none", "typeerror", "default", "get", "missing", "key", "multiply"],
    },
    {
        "id": "wrong_argument_order",
        "code": (
            "from datetime import timedelta\n\n"
            "def schedule_retry(delay_seconds: int):\n"
            "    delta = timedelta(delay_seconds)\n"
            "    return get_now() + delta"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "timedelta(n) sets days=n, not seconds — use timedelta(seconds=delay_seconds)",
        "issue_keywords": ["timedelta", "days", "seconds", "wrong", "argument", "keyword", "positional"],
    },
    {
        "id": "chained_comparison_and",
        "code": (
            "def is_valid_port(port) -> bool:\n"
            "    return 1 <= port <= 65535 and port != None"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "port != None must come first — chained comparison 1 <= None raises TypeError",
        "issue_keywords": ["none", "typeerror", "order", "comparison", "guard", "check", "is not"],
    },
    {
        "id": "async_sleep_blocking",
        "code": (
            "import asyncio, time\n\n"
            "async def rate_limited_fetch(url: str) -> str:\n"
            "    time.sleep(0.5)\n"
            "    return await fetch(url)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "time.sleep in async function blocks the event loop — use await asyncio.sleep(0.5)",
        "issue_keywords": ["block", "event loop", "asyncio.sleep", "time.sleep", "async", "await", "coroutine"],
    },
    {
        "id": "uninitialized_variable_path",
        "code": (
            "def compute_result(data: list) -> float:\n"
            "    if data:\n"
            "        result = sum(data) / len(data)\n"
            "    return result"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "result referenced before assignment when data is empty — UnboundLocalError",
        "issue_keywords": ["unboundlocal", "uninitialized", "empty", "result", "assign", "error", "guard"],
    },
    {
        "id": "format_string_wrong_type",
        "code": (
            "def format_price(amount: float, currency: str = 'USD') -> str:\n"
            "    return f'{currency}: {amount:d}'"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": ":d format specifier requires integer — raises ValueError for float amount",
        "issue_keywords": ["format", "valueerror", ":d", "integer", "float", "specifier", "wrong"],
    },
    {
        "id": "wrong_max_min",
        "code": (
            "def clamp(value: float, lo: float, hi: float) -> float:\n"
            "    return max(lo, min(lo, value))"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "min(lo, value) uses lo twice — should be min(hi, value); clamping always returns lo",
        "issue_keywords": ["wrong", "clamp", "max", "min", "hi", "lo", "typo"],
    },
    {
        "id": "zip_unequal_lengths",
        "code": (
            "def pair_scores(names: list, scores: list) -> dict:\n"
            "    return dict(zip(names, scores))"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "zip silently truncates to shorter list — mismatched lengths lose data with no error",
        "issue_keywords": ["zip", "truncat", "length", "mismatch", "silent", "zip_longest", "assert"],
    },
    {
        "id": "dataclass_frozen_field",
        "code": (
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class Point:\n"
            "    x: float\n"
            "    y: float\n"
            "    history: list = []\n\n"
            "    def move(self, dx, dy):\n"
            "        self.history.append((self.x, self.y))\n"
            "        self.x += dx\n"
            "        self.y += dy"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Mutable list default in dataclass field — all Point instances share same history list",
        "issue_keywords": ["mutable", "default", "shared", "field", "dataclass", "list", "factory"],
    },
    {
        "id": "exception_variable_scope",
        "code": (
            "def process(data):\n"
            "    try:\n"
            "        result = compute(data)\n"
            "    except ValueError as e:\n"
            "        log_error(e)\n"
            "    print(e)"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Exception variable e is deleted after except block — NameError outside the block",
        "issue_keywords": ["nameerror", "scope", "exception", "variable", "deleted", "outside", "block"],
    },
    {
        "id": "wrong_json_key_access",
        "code": (
            "import json\n\n"
            "def get_user_name(json_str: str) -> str:\n"
            "    data = json.loads(json_str)\n"
            "    return data['user']['name']"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "KeyError when 'user' or 'name' missing — no guard for optional or partial JSON structures",
        "issue_keywords": ["keyerror", "missing", "guard", "get", "check", "optional", "json"],
    },
    {
        "id": "modulo_negative",
        "code": (
            "def wrap_index(idx: int, size: int) -> int:\n"
            "    if idx >= size:\n"
            "        return idx - size\n"
            "    return idx"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Doesn't handle idx > 2*size or negative idx — use idx % size instead",
        "issue_keywords": ["modulo", "wrap", "negative", "bound", "overflow", "incorrect", "edge"],
    },

    # ════════════════════════════════════════════════════════════════════════
    # MAINTAINABILITY  (45 tasks)
    # ════════════════════════════════════════════════════════════════════════

    {
        "id": "n_plus_one_query",
        "code": (
            "def get_orders_with_items(user_id: int) -> list:\n"
            "    orders = db.query('SELECT * FROM orders WHERE user_id=?', user_id)\n"
            "    for order in orders:\n"
            "        order['items'] = db.query('SELECT * FROM items WHERE order_id=?', order['id'])\n"
            "    return orders"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "N+1 query problem — one extra DB query per order; use JOIN or batch fetch",
        "issue_keywords": ["n+1", "query", "loop", "batch", "join", "performance", "inefficient"],
    },
    {
        "id": "god_function",
        "code": (
            "def process_user_signup(data: dict) -> dict:\n"
            "    # validate input\n"
            "    if not data.get('email') or '@' not in data['email']:\n"
            "        raise ValueError('bad email')\n"
            "    # hash password\n"
            "    pw_hash = hashlib.sha256(data['password'].encode()).hexdigest()\n"
            "    # store in DB\n"
            "    user_id = db.insert('users', email=data['email'], pw=pw_hash)\n"
            "    # send welcome email\n"
            "    smtp.send(data['email'], 'Welcome!')\n"
            "    # create free trial\n"
            "    billing.create_trial(user_id)\n"
            "    # log event\n"
            "    analytics.track('signup', user_id)\n"
            "    return {'id': user_id}"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "God function with 6 distinct responsibilities — untestable, fragile, violates single-responsibility",
        "issue_keywords": ["responsib", "single", "refactor", "god", "function", "testab", "coupling"],
    },
    {
        "id": "socket_not_closed",
        "code": (
            "import socket\n\n"
            "def send_ping(host: str, port: int) -> bool:\n"
            "    s = socket.socket()\n"
            "    s.connect((host, port))\n"
            "    s.send(b'PING')\n"
            "    return s.recv(4) == b'PONG'"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Socket never closed — resource leak on every call, especially on exception path",
        "issue_keywords": ["close", "leak", "resource", "context", "with ", "socket", "finally"],
    },
    {
        "id": "deeply_nested_conditional",
        "code": (
            "def process(data):\n"
            "    if data:\n"
            "        if data.get('active'):\n"
            "            if data.get('role') == 'admin':\n"
            "                if data.get('permissions'):\n"
            "                    return execute(data)\n"
            "    return None"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "4-level nesting — use early returns (guard clauses) to flatten pyramid of doom",
        "issue_keywords": ["nested", "deep", "pyramid", "guard", "early return", "readab", "flatten"],
    },
    {
        "id": "print_debug_statements",
        "code": (
            "def calculate_shipping(weight: float, distance: float) -> float:\n"
            "    base = weight * 0.5\n"
            "    print(f'DEBUG: base={base}')\n"
            "    adjusted = base * (1 + distance / 1000)\n"
            "    print(f'DEBUG: adjusted={adjusted}')\n"
            "    return adjusted"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Debug print statements left in production code — use logging module with appropriate level",
        "issue_keywords": ["debug", "print", "log", "produc", "remov", "logging", "leak"],
    },
    {
        "id": "ignored_return_value",
        "code": (
            "def update_user_email(user_id: int, new_email: str):\n"
            "    db.execute('UPDATE users SET email=? WHERE id=?', new_email, user_id)\n"
            "    return True"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "No check on rows affected — returns True even when user_id doesn't exist",
        "issue_keywords": ["rowcount", "affected", "check", "return", "exist", "verify", "update"],
    },
    {
        "id": "catch_and_ignore",
        "code": (
            "def load_plugin(name: str):\n"
            "    try:\n"
            "        module = importlib.import_module(f'plugins.{name}')\n"
            "        return module.init()\n"
            "    except Exception:\n"
            "        pass"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Bare pass in except silently swallows all errors — ImportError and init failures invisible",
        "issue_keywords": ["swallow", "silent", "pass", "except", "log", "bare", "ignore"],
    },
    {
        "id": "flag_argument_coupling",
        "code": (
            "def save_data(data: dict, dry_run: bool = False, verbose: bool = False,\n"
            "              validate: bool = True, overwrite: bool = False):\n"
            "    if validate:\n"
            "        check(data)\n"
            "    if not dry_run:\n"
            "        write(data, overwrite=overwrite)\n"
            "    if verbose:\n"
            "        print('saved')"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Multiple boolean flags create 16 combinations — split into focused functions",
        "issue_keywords": ["flag", "boolean", "combinat", "split", "refactor", "responsib", "coupling"],
    },
    {
        "id": "hardcoded_magic_timeout",
        "code": (
            "import requests\n\n"
            "def fetch_report(url: str) -> dict:\n"
            "    resp = requests.get(url, timeout=30)\n"
            "    resp.raise_for_status()\n"
            "    return resp.json()"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Magic number 30 for timeout — should be a named constant configurable per environment",
        "issue_keywords": ["magic", "constant", "config", "named", "timeout", "hardcod", "literal"],
    },
    {
        "id": "unused_variable",
        "code": (
            "def compute_stats(values: list) -> dict:\n"
            "    n = len(values)\n"
            "    mean = sum(values) / n\n"
            "    median = sorted(values)[n // 2]\n"
            "    variance = sum((x - mean) ** 2 for x in values) / n\n"
            "    std = variance ** 0.5\n"
            "    result = {'mean': mean, 'std': std}\n"
            "    return result"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "median computed but never used or returned — dead code adds confusion",
        "issue_keywords": ["unused", "dead code", "median", "never used", "variable", "confus", "return"],
    },
    {
        "id": "string_format_inconsistency",
        "code": (
            "def build_url(base: str, path: str, param: str) -> str:\n"
            "    step1 = base + '/' + path\n"
            "    step2 = step1 + '?q=' + param\n"
            "    return '%s' % step2"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Three different string formatting styles in one function — use f-string or urllib.parse.urljoin",
        "issue_keywords": ["inconsistent", "format", "style", "f-string", "readab", "concatenat", "urljoin"],
    },
    {
        "id": "overlong_function",
        "code": (
            "def validate_and_save_profile(user_id, name, email, phone,\n"
            "                              address, bio, avatar_url, preferences):\n"
            "    if len(name) < 2 or len(name) > 50:\n"
            "        raise ValueError('name length')\n"
            "    if '@' not in email:\n"
            "        raise ValueError('bad email')\n"
            "    if phone and not phone.replace('+','').replace('-','').isdigit():\n"
            "        raise ValueError('bad phone')\n"
            "    if len(bio or '') > 500:\n"
            "        raise ValueError('bio too long')\n"
            "    db.update_profile(user_id, name, email, phone, address, bio, avatar_url, preferences)\n"
            "    cache.invalidate(f'profile:{user_id}')"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "8-parameter function doing validation + persistence + cache invalidation — should be split",
        "issue_keywords": ["parameter", "responsib", "split", "refactor", "validat", "coupling", "length"],
    },
    {
        "id": "db_connection_in_loop",
        "code": (
            "def archive_old_records(ids: list):\n"
            "    for record_id in ids:\n"
            "        conn = get_db_connection()\n"
            "        conn.execute('UPDATE records SET archived=1 WHERE id=?', record_id)\n"
            "        conn.close()"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "New DB connection per loop iteration — expensive overhead; use single connection outside loop",
        "issue_keywords": ["connection", "loop", "per.iteration", "overhead", "pool", "outside", "inefficient"],
    },
    {
        "id": "exception_type_too_broad",
        "code": (
            "def read_config(path: str) -> dict:\n"
            "    try:\n"
            "        with open(path) as f:\n"
            "            return json.load(f)\n"
            "    except Exception as e:\n"
            "        logger.error(f'Config error: {e}')\n"
            "        return {}"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Catching Exception masks FileNotFoundError vs JSONDecodeError — different recovery paths warranted",
        "issue_keywords": ["broad", "specific", "exception", "filenotfound", "json", "mask", "catch"],
    },
    {
        "id": "todo_comment_blocking",
        "code": (
            "def authenticate(username: str, password: str) -> bool:\n"
            "    # TODO: add brute-force protection\n"
            "    # TODO: implement account lockout\n"
            "    user = db.get_user(username)\n"
            "    if user is None:\n"
            "        return False\n"
            "    return check_password(password, user['pw_hash'])"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Critical security TODOs in authentication code — brute force and lockout not implemented",
        "issue_keywords": ["todo", "brute.force", "lockout", "implement", "missing", "security", "comment"],
    },
    {
        "id": "class_without_repr",
        "code": (
            "class DatabaseError(Exception):\n"
            "    def __init__(self, msg: str, query: str, params: tuple):\n"
            "        self.msg = msg\n"
            "        self.query = query\n"
            "        self.params = params\n"
            "        super().__init__(msg)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Custom exception stores query and params but no __repr__ — debugging shows only msg",
        "issue_keywords": ["repr", "__repr__", "debug", "inspect", "display", "context", "missing"],
    },
    {
        "id": "import_inside_hot_path",
        "code": (
            "def format_timestamp(ts: float) -> str:\n"
            "    import datetime\n"
            "    return datetime.datetime.utcfromtimestamp(ts).isoformat()"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Import inside function called on hot path — module lookup overhead on every call; move to top-level",
        "issue_keywords": ["import", "inside", "function", "top.level", "overhead", "hot.path", "performance"],
    },
    {
        "id": "truncated_error_message",
        "code": (
            "def call_api(endpoint: str, payload: dict) -> dict:\n"
            "    resp = requests.post(endpoint, json=payload)\n"
            "    if resp.status_code != 200:\n"
            "        raise RuntimeError('API call failed')\n"
            "    return resp.json()"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Error message omits status code and response body — impossible to debug without re-running",
        "issue_keywords": ["error message", "status", "context", "debug", "body", "include", "information"],
    },
    {
        "id": "no_input_validation_public",
        "code": (
            "def set_log_level(level: int):\n"
            "    logging.root.setLevel(level)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "No validation of level — arbitrary int silently accepted; should check against valid levels",
        "issue_keywords": ["valida", "input", "level", "check", "public", "boundary", "assert"],
    },
    {
        "id": "class_variable_vs_instance",
        "code": (
            "class RequestTracker:\n"
            "    request_count = 0\n\n"
            "    def track(self):\n"
            "        self.request_count += 1\n"
            "        return self.request_count"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "self.request_count += 1 creates instance variable shadowing class variable — confusing semantics",
        "issue_keywords": ["class variable", "instance", "shadow", "confus", "semantic", "attribute", "shared"],
    },
    {
        "id": "return_none_explicitly",
        "code": (
            "def update_cache(key: str, value) -> None:\n"
            "    if not key:\n"
            "        return None\n"
            "    cache[key] = value\n"
            "    return None"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Explicit return None adds noise — implicit return is idiomatic Python for void functions",
        "issue_keywords": ["return none", "explicit", "implicit", "idiom", "void", "unnecessary", "noise"],
    },
    {
        "id": "unnecessary_else_after_return",
        "code": (
            "def grade(score: int) -> str:\n"
            "    if score >= 90:\n"
            "        return 'A'\n"
            "    else:\n"
            "        if score >= 80:\n"
            "            return 'B'\n"
            "        else:\n"
            "            return 'C'"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Unnecessary else after return — elif chain removes nesting and is more readable",
        "issue_keywords": ["else", "return", "unnecessary", "elif", "readab", "flatten", "nest"],
    },
    {
        "id": "string_in_bool_context",
        "code": (
            "def is_feature_enabled(flag: str) -> bool:\n"
            "    return bool(flag)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "bool('false') returns True — non-empty string is always truthy regardless of content",
        "issue_keywords": ["truthy", "false", "bool", "string", "empty", "wrong", "confus"],
    },
    {
        "id": "file_open_no_encoding",
        "code": (
            "def read_text_file(path: str) -> str:\n"
            "    with open(path) as f:\n"
            "        return f.read()"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "No encoding specified — behaviour differs across OS/locale; always pass encoding='utf-8'",
        "issue_keywords": ["encoding", "utf-8", "locale", "platform", "specify", "portab", "open"],
    },
    {
        "id": "chained_string_replace",
        "code": (
            "def clean_text(text: str) -> str:\n"
            "    return text.replace('  ', ' ').replace('  ', ' ').replace('\\t', ' ').replace('\\n', ' ')"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Chained replaces create multiple string copies and still misses triple spaces; use re.sub",
        "issue_keywords": ["chain", "replace", "readab", "re.sub", "regex", "inefficient", "whitespace"],
    },
    {
        "id": "mixed_return_types",
        "code": (
            "def get_user(user_id: int):\n"
            "    if user_id <= 0:\n"
            "        return False\n"
            "    user = db.find(user_id)\n"
            "    if user is None:\n"
            "        return None\n"
            "    return user"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Returns False, None, or dict — inconsistent types force callers to handle 3 cases",
        "issue_keywords": ["return type", "inconsistent", "union", "optional", "caller", "confus", "mixed"],
    },
    {
        "id": "recompute_in_loop",
        "code": (
            "def filter_active(users: list) -> list:\n"
            "    return [u for u in users if u['status'] in ['active', 'trial', 'grace']]\n\n"
            "def count_active(users: list) -> int:\n"
            "    return len([u for u in users if u['status'] in ['active', 'trial', 'grace']])"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Filter logic duplicated in two places — extract constant set and shared helper",
        "issue_keywords": ["duplicat", "DRY", "constant", "extract", "helper", "refactor", "repeat"],
    },
    {
        "id": "global_mutable_config",
        "code": (
            "CONFIG = {\n"
            "    'db_url': 'sqlite:///local.db',\n"
            "    'debug': False,\n"
            "}\n\n"
            "def set_debug(value: bool):\n"
            "    CONFIG['debug'] = value"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Mutable global config mutated at runtime — thread-unsafe, test order-dependent",
        "issue_keywords": ["global", "mutable", "config", "thread", "test", "side.effect", "inject"],
    },
    {
        "id": "nested_list_comprehension_unreadable",
        "code": (
            "def flatten_matrix(matrix: list) -> list:\n"
            "    return [cell for row in matrix for cell in row if cell is not None]"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Multi-clause comprehension with filter is hard to read — use explicit loop or comment",
        "issue_keywords": ["readab", "comprehension", "complex", "loop", "comment", "clarity", "nested"],
    },
    {
        "id": "boolean_comparison_to_true",
        "code": (
            "def check_flag(config: dict) -> bool:\n"
            "    if config.get('enabled') == True:\n"
            "        return True\n"
            "    return False"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "== True is redundant and non-idiomatic; the entire function can be bool(config.get('enabled'))",
        "issue_keywords": ["== True", "redundant", "idiom", "bool", "simplif", "readab", "unnecessary"],
    },
    {
        "id": "property_with_side_effect",
        "code": (
            "class Report:\n"
            "    @property\n"
            "    def data(self):\n"
            "        self._access_count += 1\n"
            "        return self._data"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Property with side effect violates principle of least surprise — callers don't expect mutation",
        "issue_keywords": ["property", "side.effect", "surprise", "mutate", "access", "principle", "unexpected"],
    },
    {
        "id": "resource_leak_exception_path",
        "code": (
            "def process_file(path: str) -> str:\n"
            "    f = open(path)\n"
            "    data = f.read()\n"
            "    result = transform(data)\n"
            "    f.close()\n"
            "    return result"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "File not closed if transform() raises — use context manager (with open(...)) for guaranteed close",
        "issue_keywords": ["leak", "close", "context", "with ", "exception", "finally", "resource"],
    },
    {
        "id": "print_to_stdout_in_lib",
        "code": (
            "def compute_risk_score(factors: list) -> float:\n"
            "    score = sum(factors) / len(factors)\n"
            "    print(f'Risk score computed: {score:.2f}')\n"
            "    return score"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Library function prints to stdout — breaks callers that redirect stdout; use logging",
        "issue_keywords": ["print", "stdout", "library", "log", "redirect", "side.effect", "caller"],
    },
    {
        "id": "long_import_chain",
        "code": (
            "from app.core.utils.helpers.formatting import format_date\n"
            "from app.core.utils.helpers.formatting import format_time\n"
            "from app.core.utils.helpers.formatting import format_currency\n"
            "from app.core.utils.helpers.formatting import format_percentage\n"
            "from app.core.utils.helpers.formatting import format_phone"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "5 imports from same deeply nested module — use single import of module or from ... import *",
        "issue_keywords": ["import", "readab", "group", "single", "refactor", "module", "consolidat"],
    },
    {
        "id": "test_without_assertion",
        "code": (
            "def test_create_user():\n"
            "    user = create_user(name='Alice', email='a@b.com')\n"
            "    print(user)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Test without assertion — always passes even if create_user returns None or raises",
        "issue_keywords": ["assert", "test", "missing", "always pass", "print", "verificat", "assertion"],
    },
    {
        "id": "catch_keyboardinterrupt",
        "code": (
            "def run_forever():\n"
            "    while True:\n"
            "        try:\n"
            "            process_next()\n"
            "        except Exception:\n"
            "            pass"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Bare except Exception swallows KeyboardInterrupt (caught by BaseException) but prevents clean shutdown signal from being visible",
        "issue_keywords": ["bare", "except", "swallow", "silent", "keyboard", "shutdown", "signal"],
    },
    {
        "id": "module_level_side_effect",
        "code": (
            "import logging\n"
            "import os\n\n"
            "logging.basicConfig(level=logging.DEBUG)\n"
            "os.makedirs('/tmp/myapp', exist_ok=True)\n\n"
            "def get_logger():\n"
            "    return logging.getLogger('myapp')"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Module-level side effects run on import — logging config and mkdir affect the whole process unexpectedly",
        "issue_keywords": ["side.effect", "import", "module.level", "logging", "makedirs", "unexpected", "global"],
    },

    # ════════════════════════════════════════════════════════════════════════
    # CLEAN  (45 tasks)
    # ════════════════════════════════════════════════════════════════════════

    {
        "id": "clean_lru_cache",
        "code": (
            "from functools import lru_cache\n\n"
            "@lru_cache(maxsize=256)\n"
            "def fibonacci(n: int) -> int:\n"
            "    if n < 2:\n"
            "        return n\n"
            "    return fibonacci(n - 1) + fibonacci(n - 2)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean memoized fibonacci with bounded cache",
        "issue_keywords": [],
    },
    {
        "id": "clean_dataclass_frozen",
        "code": (
            "from dataclasses import dataclass, field\n\n"
            "@dataclass(frozen=True)\n"
            "class Money:\n"
            "    amount: int\n"
            "    currency: str\n\n"
            "    def __add__(self, other: 'Money') -> 'Money':\n"
            "        if self.currency != other.currency:\n"
            "            raise ValueError(f'Cannot add {self.currency} and {other.currency}')\n"
            "        return Money(self.amount + other.amount, self.currency)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean frozen dataclass value type with currency guard",
        "issue_keywords": [],
    },
    {
        "id": "clean_enum_methods",
        "code": (
            "from enum import Enum\n\n"
            "class HttpStatus(Enum):\n"
            "    OK = 200\n"
            "    NOT_FOUND = 404\n"
            "    SERVER_ERROR = 500\n\n"
            "    def is_success(self) -> bool:\n"
            "        return 200 <= self.value < 300\n\n"
            "    def is_error(self) -> bool:\n"
            "        return self.value >= 400"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean enum with behavior methods — no magic numbers in callers",
        "issue_keywords": [],
    },
    {
        "id": "clean_pathlib_usage",
        "code": (
            "from pathlib import Path\n\n"
            "def read_config(base_dir: Path, name: str) -> str:\n"
            "    config_path = base_dir / 'config' / f'{name}.json'\n"
            "    if not config_path.is_file():\n"
            "        raise FileNotFoundError(f'Config not found: {config_path}')\n"
            "    return config_path.read_text(encoding='utf-8')"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean pathlib path composition with explicit encoding and guard",
        "issue_keywords": [],
    },
    {
        "id": "clean_abc_interface",
        "code": (
            "from abc import ABC, abstractmethod\n\n"
            "class Serializer(ABC):\n"
            "    @abstractmethod\n"
            "    def serialize(self, obj: dict) -> bytes:\n"
            "        ...\n\n"
            "    @abstractmethod\n"
            "    def deserialize(self, data: bytes) -> dict:\n"
            "        ..."
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean abstract base class defining interface contract",
        "issue_keywords": [],
    },
    {
        "id": "clean_protocol_typing",
        "code": (
            "from typing import Protocol\n\n"
            "class Closeable(Protocol):\n"
            "    def close(self) -> None:\n"
            "        ...\n\n"
            "def cleanup(resource: Closeable) -> None:\n"
            "    resource.close()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean structural subtyping with Protocol — no inheritance required",
        "issue_keywords": [],
    },
    {
        "id": "clean_generator_pipeline",
        "code": (
            "from typing import Iterable\n\n"
            "def read_lines(path: str) -> Iterable[str]:\n"
            "    with open(path, encoding='utf-8') as f:\n"
            "        yield from f\n\n"
            "def parse_records(lines: Iterable[str]) -> Iterable[dict]:\n"
            "    import json\n"
            "    for line in lines:\n"
            "        line = line.strip()\n"
            "        if line:\n"
            "            yield json.loads(line)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean generator pipeline — lazy, memory-efficient, composable",
        "issue_keywords": [],
    },
    {
        "id": "clean_slots_class",
        "code": (
            "class Vector2D:\n"
            "    __slots__ = ('x', 'y')\n\n"
            "    def __init__(self, x: float, y: float):\n"
            "        self.x = x\n"
            "        self.y = y\n\n"
            "    def magnitude(self) -> float:\n"
            "        return (self.x ** 2 + self.y ** 2) ** 0.5"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean __slots__ class for memory-efficient value objects",
        "issue_keywords": [],
    },
    {
        "id": "clean_typeddict",
        "code": (
            "from typing import TypedDict, Optional\n\n"
            "class UserRecord(TypedDict):\n"
            "    id: int\n"
            "    email: str\n"
            "    name: str\n"
            "    role: str\n\n"
            "class PartialUpdate(TypedDict, total=False):\n"
            "    email: str\n"
            "    name: str"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean TypedDict definitions for typed dict structures",
        "issue_keywords": [],
    },
    {
        "id": "clean_context_manager_class",
        "code": (
            "class Timer:\n"
            "    def __enter__(self):\n"
            "        import time\n"
            "        self._start = time.perf_counter()\n"
            "        return self\n\n"
            "    def __exit__(self, *_):\n"
            "        import time\n"
            "        self.elapsed = time.perf_counter() - self._start\n"
            "        return False"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean context manager class — does not suppress exceptions (returns False)",
        "issue_keywords": [],
    },
    {
        "id": "clean_sentinel_pattern",
        "code": (
            "_MISSING = object()\n\n"
            "def get_env(key: str, default=_MISSING) -> str:\n"
            "    import os\n"
            "    val = os.environ.get(key, _MISSING)\n"
            "    if val is _MISSING:\n"
            "        if default is _MISSING:\n"
            "            raise KeyError(f'Required env var {key!r} not set')\n"
            "        return default\n"
            "    return val"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean sentinel pattern — distinguishes missing from None as explicit default",
        "issue_keywords": [],
    },
    {
        "id": "clean_functools_partial",
        "code": (
            "from functools import partial\n"
            "import json\n\n"
            "compact_json = partial(json.dumps, separators=(',', ':'), sort_keys=True)\n"
            "pretty_json  = partial(json.dumps, indent=2, sort_keys=True)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean use of functools.partial to create specialized serializers",
        "issue_keywords": [],
    },
    {
        "id": "clean_walrus_operator",
        "code": (
            "import re\n\n"
            "def extract_version(text: str) -> str | None:\n"
            "    if m := re.search(r'v(\\d+\\.\\d+\\.\\d+)', text):\n"
            "        return m.group(1)\n"
            "    return None"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean walrus operator usage — readable and avoids double regex match",
        "issue_keywords": [],
    },
    {
        "id": "clean_custom_exception_hierarchy",
        "code": (
            "class AppError(Exception):\n"
            "    pass\n\n"
            "class ValidationError(AppError):\n"
            "    def __init__(self, field: str, message: str):\n"
            "        self.field = field\n"
            "        super().__init__(f'{field}: {message}')\n\n"
            "class NotFoundError(AppError):\n"
            "    def __init__(self, resource: str, identifier):\n"
            "        super().__init__(f'{resource} {identifier!r} not found')"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean exception hierarchy with informative messages and structured data",
        "issue_keywords": [],
    },
    {
        "id": "clean_named_tuple_return",
        "code": (
            "from typing import NamedTuple\n\n"
            "class ParseResult(NamedTuple):\n"
            "    host: str\n"
            "    port: int\n"
            "    path: str\n\n"
            "def parse_endpoint(endpoint: str) -> ParseResult:\n"
            "    host, rest = endpoint.split('/', 1)\n"
            "    host, port_str = host.rsplit(':', 1)\n"
            "    return ParseResult(host=host, port=int(port_str), path='/' + rest)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean NamedTuple return type — readable, typed, unpackable",
        "issue_keywords": [],
    },
    {
        "id": "clean_cached_property",
        "code": (
            "from functools import cached_property\n\n"
            "class Document:\n"
            "    def __init__(self, text: str):\n"
            "        self.text = text\n\n"
            "    @cached_property\n"
            "    def word_count(self) -> int:\n"
            "        return len(self.text.split())"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean cached_property — computed once, stored on instance, no manual caching needed",
        "issue_keywords": [],
    },
    {
        "id": "clean_dataclass_post_init",
        "code": (
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class EmailAddress:\n"
            "    value: str\n\n"
            "    def __post_init__(self):\n"
            "        self.value = self.value.strip().lower()\n"
            "        if '@' not in self.value:\n"
            "            raise ValueError(f'Invalid email: {self.value!r}')"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean dataclass with __post_init__ validation and normalisation",
        "issue_keywords": [],
    },
    {
        "id": "clean_iter_protocol",
        "code": (
            "class NumberRange:\n"
            "    def __init__(self, start: int, stop: int):\n"
            "        self.start = start\n"
            "        self.stop = stop\n\n"
            "    def __iter__(self):\n"
            "        current = self.start\n"
            "        while current < self.stop:\n"
            "            yield current\n"
            "            current += 1\n\n"
            "    def __len__(self) -> int:\n"
            "        return max(0, self.stop - self.start)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean iterator protocol implementation with __len__",
        "issue_keywords": [],
    },
    {
        "id": "clean_secrets_token",
        "code": (
            "import secrets\n\n"
            "def generate_api_key(prefix: str = 'sk') -> str:\n"
            "    token = secrets.token_urlsafe(32)\n"
            "    return f'{prefix}_{token}'"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct CSPRNG token generation using secrets module",
        "issue_keywords": [],
    },
    {
        "id": "clean_pydantic_model",
        "code": (
            "from pydantic import BaseModel, EmailStr, field_validator\n\n"
            "class UserCreate(BaseModel):\n"
            "    name: str\n"
            "    email: EmailStr\n"
            "    age: int\n\n"
            "    @field_validator('age')\n"
            "    @classmethod\n"
            "    def age_must_be_positive(cls, v: int) -> int:\n"
            "        if v < 0:\n"
            "            raise ValueError('age must be non-negative')\n"
            "        return v"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean Pydantic model with validated email and custom age validator",
        "issue_keywords": [],
    },
    {
        "id": "clean_async_context_manager",
        "code": (
            "from contextlib import asynccontextmanager\n\n"
            "@asynccontextmanager\n"
            "async def managed_session(client):\n"
            "    session = await client.open_session()\n"
            "    try:\n"
            "        yield session\n"
            "    finally:\n"
            "        await session.close()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean async context manager with guaranteed close in finally",
        "issue_keywords": [],
    },
    {
        "id": "clean_heapq_nlargest",
        "code": (
            "import heapq\n\n"
            "def top_n_scores(scores: list[int], n: int) -> list[int]:\n"
            "    if n >= len(scores):\n"
            "        return sorted(scores, reverse=True)\n"
            "    return heapq.nlargest(n, scores)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct heapq.nlargest with edge case handling for n >= len",
        "issue_keywords": [],
    },
    {
        "id": "clean_chain_map",
        "code": (
            "from collections import ChainMap\n\n"
            "def resolve_config(user_cfg: dict, env_cfg: dict, defaults: dict) -> dict:\n"
            "    return dict(ChainMap(user_cfg, env_cfg, defaults))"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean config layering with ChainMap — priority order preserved, originals unchanged",
        "issue_keywords": [],
    },
    {
        "id": "clean_parameterized_fixture",
        "code": (
            "import pytest\n\n"
            "@pytest.mark.parametrize('value,expected', [\n"
            "    (0,   True),\n"
            "    (1,   False),\n"
            "    (-1,  False),\n"
            "    (100, False),\n"
            "])\n"
            "def test_is_zero(value: int, expected: bool):\n"
            "    assert is_zero(value) == expected"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean parametrized pytest test covering edge cases",
        "issue_keywords": [],
    },
    {
        "id": "clean_decimal_currency",
        "code": (
            "from decimal import Decimal, ROUND_HALF_UP\n\n"
            "def apply_tax(amount: Decimal, rate: Decimal) -> Decimal:\n"
            "    tax = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)\n"
            "    return amount + tax"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct currency arithmetic using Decimal with explicit rounding",
        "issue_keywords": [],
    },
    {
        "id": "clean_thread_local",
        "code": (
            "import threading\n\n"
            "_local = threading.local()\n\n"
            "def get_request_context() -> dict:\n"
            "    if not hasattr(_local, 'context'):\n"
            "        _local.context = {}\n"
            "    return _local.context"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean thread-local storage pattern — each thread has isolated context",
        "issue_keywords": [],
    },
    {
        "id": "clean_contextvar",
        "code": (
            "from contextvars import ContextVar\n\n"
            "request_id: ContextVar[str] = ContextVar('request_id', default='')\n\n"
            "def set_request_id(rid: str):\n"
            "    return request_id.set(rid)\n\n"
            "def get_request_id() -> str:\n"
            "    return request_id.get()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean ContextVar usage for async-safe request scoping",
        "issue_keywords": [],
    },
    {
        "id": "clean_bisect_search",
        "code": (
            "import bisect\n\n"
            "def find_grade(score: int, breakpoints: list, grades: list) -> str:\n"
            "    i = bisect.bisect_right(breakpoints, score)\n"
            "    return grades[i]"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean bisect_right for grade lookup — O(log n), no if-elif chain",
        "issue_keywords": [],
    },
    {
        "id": "clean_zip_strict",
        "code": (
            "def pair_headers_values(headers: list[str], values: list) -> dict:\n"
            "    return dict(zip(headers, values, strict=True))"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "zip with strict=True raises ValueError on length mismatch — correct defensive pairing",
        "issue_keywords": [],
    },
    {
        "id": "clean_slots_dataclass",
        "code": (
            "from dataclasses import dataclass\n\n"
            "@dataclass(slots=True)\n"
            "class Coordinate:\n"
            "    lat: float\n"
            "    lon: float\n"
            "    alt: float = 0.0\n\n"
            "    def to_tuple(self) -> tuple[float, float, float]:\n"
            "        return (self.lat, self.lon, self.alt)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean dataclass with slots=True for memory efficiency — Python 3.10+",
        "issue_keywords": [],
    },
    {
        "id": "clean_abstractproperty",
        "code": (
            "from abc import ABC, abstractmethod\n\n"
            "class Shape(ABC):\n"
            "    @property\n"
            "    @abstractmethod\n"
            "    def area(self) -> float:\n"
            "        ...\n\n"
            "    @property\n"
            "    @abstractmethod\n"
            "    def perimeter(self) -> float:\n"
            "        ..."
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean abstract property definition using @property + @abstractmethod",
        "issue_keywords": [],
    },
    {
        "id": "clean_more_itertools_chunk",
        "code": (
            "def chunked(iterable, size: int):\n"
            "    it = iter(iterable)\n"
            "    while True:\n"
            "        chunk = []\n"
            "        try:\n"
            "            for _ in range(size):\n"
            "                chunk.append(next(it))\n"
            "        except StopIteration:\n"
            "            if chunk:\n"
            "                yield chunk\n"
            "            return\n"
            "        yield chunk"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean chunked iterator — handles partial final chunk and empty iterables",
        "issue_keywords": [],
    },
    {
        "id": "clean_hmac_comparison",
        "code": (
            "import hmac\n\n"
            "def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:\n"
            "    expected = hmac.new(secret.encode(), payload, 'sha256').hexdigest()\n"
            "    return hmac.compare_digest(expected, signature)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct constant-time HMAC verification using compare_digest",
        "issue_keywords": [],
    },
    {
        "id": "clean_environ_get_with_default",
        "code": (
            "import os\n\n"
            "DB_HOST     = os.environ.get('DB_HOST', 'localhost')\n"
            "DB_PORT     = int(os.environ.get('DB_PORT', '5432'))\n"
            "DB_NAME     = os.environ.get('DB_NAME', 'app')\n"
            "DB_POOL_MAX = int(os.environ.get('DB_POOL_MAX', '10'))"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean environment variable config with typed defaults — no hardcoded credentials",
        "issue_keywords": [],
    },
    {
        "id": "clean_dataclass_validator",
        "code": (
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class Port:\n"
            "    number: int\n\n"
            "    def __post_init__(self):\n"
            "        if not 1 <= self.number <= 65535:\n"
            "            raise ValueError(f'Port must be 1-65535, got {self.number}')"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean value object with validated range in __post_init__",
        "issue_keywords": [],
    },
    {
        "id": "clean_singledispatch",
        "code": (
            "from functools import singledispatch\n\n"
            "@singledispatch\n"
            "def serialize(value) -> str:\n"
            "    return str(value)\n\n"
            "@serialize.register(list)\n"
            "def _(value: list) -> str:\n"
            "    return '[' + ', '.join(serialize(v) for v in value) + ']'\n\n"
            "@serialize.register(dict)\n"
            "def _(value: dict) -> str:\n"
            "    pairs = ', '.join(f'{k}: {serialize(v)}' for k, v in value.items())\n"
            "    return '{' + pairs + '}'"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean singledispatch for type-based dispatch without isinstance chains",
        "issue_keywords": [],
    },
    {
        "id": "clean_logging_structured",
        "code": (
            "import logging\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "def process_payment(order_id: str, amount: float):\n"
            "    logger.info('Processing payment', extra={'order_id': order_id, 'amount': amount})\n"
            "    result = charge(order_id, amount)\n"
            "    logger.info('Payment complete', extra={'order_id': order_id, 'txn_id': result.txn_id})\n"
            "    return result"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean structured logging with named logger and extra context — no print statements",
        "issue_keywords": [],
    },
    {
        "id": "clean_type_guard",
        "code": (
            "from typing import TypeGuard\n\n"
            "def is_string_list(val: list) -> TypeGuard[list[str]]:\n"
            "    return all(isinstance(item, str) for item in val)\n\n"
            "def join_tags(tags: list) -> str:\n"
            "    if not is_string_list(tags):\n"
            "        raise TypeError('tags must be a list of strings')\n"
            "    return ', '.join(tags)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean TypeGuard narrowing function with runtime validation",
        "issue_keywords": [],
    },
    {
        "id": "clean_class_method_factory",
        "code": (
            "from __future__ import annotations\n"
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class Color:\n"
            "    r: int\n"
            "    g: int\n"
            "    b: int\n\n"
            "    @classmethod\n"
            "    def from_hex(cls, hex_str: str) -> Color:\n"
            "        hex_str = hex_str.lstrip('#')\n"
            "        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)\n"
            "        return cls(r, g, b)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean classmethod factory for alternative constructor",
        "issue_keywords": [],
    },
    {
        "id": "clean_parameterized_query",
        "code": (
            "def get_user_orders(conn, user_id: int, status: str) -> list:\n"
            "    cursor = conn.cursor()\n"
            "    cursor.execute(\n"
            "        'SELECT * FROM orders WHERE user_id = ? AND status = ?',\n"
            "        (user_id, status)\n"
            "    )\n"
            "    return cursor.fetchall()"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Correct parameterized query — no string interpolation, no SQL injection risk",
        "issue_keywords": [],
    },
    {
        "id": "clean_total_ordering",
        "code": (
            "from functools import total_ordering\n\n"
            "@total_ordering\n"
            "class Version:\n"
            "    def __init__(self, major: int, minor: int, patch: int):\n"
            "        self.version = (major, minor, patch)\n\n"
            "    def __eq__(self, other) -> bool:\n"
            "        return self.version == other.version\n\n"
            "    def __lt__(self, other) -> bool:\n"
            "        return self.version < other.version"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean total_ordering — defines all comparison operators from __eq__ and __lt__",
        "issue_keywords": [],
    },

    # ── 16 gap-fill tasks to reach 200 total ─────────────────────────────────

    # Security (1)
    {
        "id": "unencrypted_pii_db",
        "code": (
            "def save_user(name: str, ssn: str, dob: str):\n"
            "    db.execute(\n"
            "        'INSERT INTO users (name, ssn, dob) VALUES (?, ?, ?)',\n"
            "        (name, ssn, dob)\n"
            "    )"
        ),
        "has_issue": True,
        "issue_type": "security",
        "severity": "critical",
        "issue_desc": "SSN and DOB stored in plaintext — PII must be encrypted at rest",
        "issue_keywords": ["encrypt", "plaintext", "pii", "sensitive", "at.rest", "ssn", "store"],
    },

    # Correctness (3)
    {
        "id": "unreachable_else_clause",
        "code": (
            "def classify(score: int) -> str:\n"
            "    if score >= 60:\n"
            "        return 'pass'\n"
            "    elif score >= 0:\n"
            "        return 'fail'\n"
            "    else:\n"
            "        return 'invalid'"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Negative scores silently return 'fail' — elif score >= 0 catches 0..59 but not negatives; else never reached",
        "issue_keywords": ["negative", "unreachable", "range", "guard", "invalid", "logic", "check"],
    },
    {
        "id": "seconds_attribute_days_bug",
        "code": (
            "from datetime import timedelta\n\n"
            "def days_until(future_ts: float, now_ts: float) -> int:\n"
            "    delta = timedelta(seconds=future_ts - now_ts)\n"
            "    return delta.seconds // 86400"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": ".seconds only counts seconds component (0-86399), not total — use .total_seconds() or .days",
        "issue_keywords": ["seconds", "total_seconds", "days", "attribute", "wrong", "component", "delta"],
    },
    {
        "id": "dict_comprehension_overwrite",
        "code": (
            "def invert_dict(d: dict) -> dict:\n"
            "    return {v: k for k, v in d.items()}"
        ),
        "has_issue": True,
        "issue_type": "correctness",
        "severity": "medium",
        "issue_desc": "Duplicate values silently overwrite earlier keys — last writer wins, data lost",
        "issue_keywords": ["duplicate", "overwrite", "value", "collision", "silent", "lost", "unique"],
    },

    # Maintainability (8)
    {
        "id": "constant_in_loop_condition",
        "code": (
            "def find_first(items: list, target: int) -> int:\n"
            "    length = len(items)\n"
            "    for i in range(len(items)):\n"
            "        if items[i] == target:\n"
            "            return i\n"
            "    return -1"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "length computed but unused — dead variable, and range(len(items)) is less idiomatic than enumerate",
        "issue_keywords": ["unused", "dead", "variable", "enumerate", "idiomatic", "redundant", "length"],
    },
    {
        "id": "lambda_instead_of_def",
        "code": (
            "process = lambda data, threshold: [\n"
            "    item for item in data\n"
            "    if item['score'] > threshold and item.get('active', False)\n"
            "]"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Named lambda assigned to variable — PEP 8 says use def; lambdas can't have docstrings",
        "issue_keywords": ["lambda", "def", "pep8", "named", "readab", "docstring", "assign"],
    },
    {
        "id": "positional_only_tuple_return",
        "code": (
            "def get_bounds(items: list) -> tuple:\n"
            "    return min(items), max(items), sum(items) / len(items)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "3-tuple return with no names — callers must know positional order; use NamedTuple or dataclass",
        "issue_keywords": ["tuple", "named", "readab", "positional", "unpack", "namedtuple", "caller"],
    },
    {
        "id": "sys_exit_in_library",
        "code": (
            "import sys\n\n"
            "def load_required_config(path: str) -> dict:\n"
            "    try:\n"
            "        return load(path)\n"
            "    except FileNotFoundError:\n"
            "        print(f'Config not found: {path}')\n"
            "        sys.exit(1)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "sys.exit in a library function kills the entire process — raise an exception instead",
        "issue_keywords": ["sys.exit", "library", "raise", "exception", "process", "kill", "caller"],
    },
    {
        "id": "inline_magic_string_comparison",
        "code": (
            "def handle_event(event: dict):\n"
            "    if event['type'] == 'user_created':\n"
            "        on_user_created(event)\n"
            "    elif event['type'] == 'user_deleted':\n"
            "        on_user_deleted(event)\n"
            "    elif event['type'] == 'user_updated':\n"
            "        on_user_updated(event)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Magic strings repeated in conditionals — use Enum or constants, and a dispatch dict",
        "issue_keywords": ["magic", "string", "constant", "enum", "dispatch", "repeat", "refactor"],
    },
    {
        "id": "no_type_hints_public_api",
        "code": (
            "def transform(data, config, mode):\n"
            "    if mode == 'fast':\n"
            "        return fast_path(data, config)\n"
            "    return slow_path(data, config)"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Public function with no type hints — callers can't tell what types are expected",
        "issue_keywords": ["type hint", "annotation", "public", "readab", "mypy", "callers", "signature"],
    },
    {
        "id": "comment_describes_what_not_why",
        "code": (
            "def paginate(items: list, page: int, size: int) -> list:\n"
            "    # multiply page by size to get start index\n"
            "    start = page * size\n"
            "    # add size to start to get end index\n"
            "    end = start + size\n"
            "    # return slice from start to end\n"
            "    return items[start:end]"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Comments restate what the code does — no page=0 vs page=1 convention documented (the actual non-obvious choice)",
        "issue_keywords": ["comment", "what", "why", "noisy", "obvious", "document", "convention"],
    },
    {
        "id": "wide_import_star",
        "code": (
            "from os.path import *\n"
            "from datetime import *\n\n"
            "def get_log_path(name: str) -> str:\n"
            "    today = date.today().strftime('%Y%m%d')\n"
            "    return join('/var/log', f'{name}_{today}.log')"
        ),
        "has_issue": True,
        "issue_type": "maintainability",
        "severity": "low",
        "issue_desc": "Wildcard imports pollute namespace — join and date are ambiguous, hides actual dependencies",
        "issue_keywords": ["wildcard", "import *", "namespace", "pollut", "ambiguous", "explicit", "star"],
    },

    # Clean (4)
    {
        "id": "clean_suppress_context",
        "code": (
            "from contextlib import suppress\n\n"
            "def safe_delete(path: str) -> bool:\n"
            "    from pathlib import Path\n"
            "    with suppress(FileNotFoundError):\n"
            "        Path(path).unlink()\n"
            "        return True\n"
            "    return False"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean use of contextlib.suppress for intentional exception suppression",
        "issue_keywords": [],
    },
    {
        "id": "clean_counter_most_common",
        "code": (
            "from collections import Counter\n\n"
            "def top_words(text: str, n: int) -> list[tuple[str, int]]:\n"
            "    words = text.lower().split()\n"
            "    return Counter(words).most_common(n)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean Counter.most_common usage — efficient, readable, correct",
        "issue_keywords": [],
    },
    {
        "id": "clean_defaultdict_groupby",
        "code": (
            "from collections import defaultdict\n\n"
            "def group_by(items: list[dict], key: str) -> dict[str, list]:\n"
            "    groups: dict[str, list] = defaultdict(list)\n"
            "    for item in items:\n"
            "        groups[item[key]].append(item)\n"
            "    return dict(groups)"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean defaultdict grouping — correct method (.append), returns plain dict",
        "issue_keywords": [],
    },
    {
        "id": "clean_dataclass_comparison",
        "code": (
            "from dataclasses import dataclass\n\n"
            "@dataclass(order=True)\n"
            "class Priority:\n"
            "    level: int\n"
            "    name: str\n\n"
            "HIGH   = Priority(level=1, name='high')\n"
            "MEDIUM = Priority(level=2, name='medium')\n"
            "LOW    = Priority(level=3, name='low')"
        ),
        "has_issue": False,
        "issue_type": "clean",
        "severity": None,
        "issue_desc": "Clean dataclass with order=True — sortable constants without manual __lt__",
        "issue_keywords": [],
    },
]
