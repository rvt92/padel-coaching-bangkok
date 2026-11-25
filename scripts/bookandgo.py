"""Read-only Book&Go client for KROSS Padel.

HARD RULE: only POST /login and GET requests are allowed. Anything else raises
before a request is sent. Credentials come from .env (username/password) or
BOOKANDGO_EMAIL / BOOKANDGO_PASSWORD and are never printed.
"""
import json, os, time, urllib.request, urllib.error
from pathlib import Path

BASE = "https://docsapi.bookandgo.app/api"
HEADERS = {"User-Agent": "KrossTool/1.0", "Accept": "application/json"}
LOCATIONS = {135: "On Nut", 136: "Indoor", 137: "Sky Club", 222: "Asoke", 290: "Kross Park"}


def _load_env():
    env = Path(__file__).resolve().parent.parent / ".env"
    vals = {}
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    email = os.environ.get("BOOKANDGO_EMAIL") or vals.get("BOOKANDGO_EMAIL") or vals.get("username")
    pw = os.environ.get("BOOKANDGO_PASSWORD") or vals.get("BOOKANDGO_PASSWORD") or vals.get("password")
    if not email or not pw:
        raise SystemExit("Missing Book&Go credentials")
    return email, pw


def _guard(method, path):
    path_only = path.split("?", 1)[0].rstrip("/")
    if method == "GET":
        return
    if method == "POST" and path_only == "/login":
        return
    raise PermissionError(f"READ-ONLY GUARD: refusing {method} {path}")


class Client:
    def __init__(self):
        self.token = None

    def _req(self, method, path, body=None):
        _guard(method, path)
        headers = dict(HEADERS)
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        last = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=90) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code in (500, 502, 503, 504, 429) and attempt < 2:
                    last = e; time.sleep(3); continue
                raise RuntimeError(f"HTTP {e.code} on {method} {path.split('?')[0]}: {e.read()[:200]!r}") from None
            except (urllib.error.URLError, TimeoutError) as e:
                last = e
                if attempt < 2:
                    time.sleep(3); continue
        raise RuntimeError(f"Request failed: {last}")

    def login(self):
        email, pw = _load_env()
        res = self._req("POST", "/login", {"email": email, "password": pw})
        self.token = res.get("token") or (res.get("data") or {}).get("token")
        if not self.token:
            raise RuntimeError("Login response had no token")

    def get(self, path):
        return self._req("GET", path)

    def bookings(self, start, end, location_id):
        return self.get(f"/bookings?start_date={start}&end_date={end}&location_id={location_id}")
