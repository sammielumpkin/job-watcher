"""One daily run: fetch every source, rebuild history from raw files, write status."""
import json
from datetime import datetime, timezone

from .fetch import fetch_all
from .history import build, raw_dates
from .sources import ROOT, load_sources
from .status import build_status, write_status

DATA = ROOT / "data"


def run(now=None, get=None):
    now = now or datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    sources = load_sources()
    kw = {"get": get} if get else {}
    results = fetch_all(sources, DATA / "raw", date, **kw)
    rows = build(DATA / "raw", DATA / "history.csv", sources)
    status = build_status(rows, raw_dates(DATA / "raw"), now.strftime("%Y-%m-%dT%H:%M:%SZ"), results)
    write_status(status, DATA / "status.json")
    # keep every day's per-source outcome (including errors); a rerun replaces that day's entry
    log_path = DATA / "run_log.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    log[date] = {"run_time": status["run_time"], "sources": results}
    log_path.write_text(json.dumps(log, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return status, results


if __name__ == "__main__":
    status, results = run()
    for r in results:
        print(("ok  " if r["ok"] else "FAIL"), f'{r["source"]:<14}{r["count"]:>5}', r["error"])
    print({k: v for k, v in status.items() if k != "sources"})
