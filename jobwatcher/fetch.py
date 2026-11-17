"""Call every source with no login, save raw JSON compressed, record each result."""
import gzip
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .convert import count_postings

HEADERS = {"User-Agent": "job-watcher/1.0 (student project)", "Accept": "application/json"}


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_one(src, get=http_get, retries=2, pause=2):
    """Return (result, raw_bytes). result = {source, name, ok, count, error}. Never raises.
    A source counts as failed when the request errors, the body is not the expected JSON,
    or it lists zero postings (an empty board is more likely a glitch than a real empty list,
    and treating it as ok would mark every posting removed)."""
    res = {"source": src["source"], "name": src["name"], "ok": False, "count": 0, "error": ""}
    for attempt in range(retries + 1):
        try:
            body = get(src["url"])
            raw = json.loads(body)
            n = count_postings(src["system"], raw)
            if n == 0:
                raise ValueError("board returned 0 postings")
            res.update(ok=True, count=n, error="")
            return res, body
        except Exception as e:  # one source failing must not stop the run
            res["error"] = f"{type(e).__name__}: {e}"[:200]
            if attempt < retries:
                time.sleep(pause)
    return res, None


def save_raw(raw_dir, date, source, body):
    d = Path(raw_dir) / date
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{source}.json.gz").write_bytes(gzip.compress(body, mtime=0))


def fetch_all(sources, raw_dir, date, get=http_get, workers=8, pause=2):
    """Fetch every source. A rerun on the same day replaces that day's raw files, so the
    day's folder is cleared first; a source that fails writes no file."""
    day = Path(raw_dir) / date
    if day.exists():
        for f in day.glob("*.json.gz"):
            f.unlink()
    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(lambda s: (s, *fetch_one(s, get, pause=pause)), sources))
    out = []
    for s, res, body in results:
        if res["ok"]:
            save_raw(raw_dir, date, s["source"], body)
        out.append(res)
    return out
