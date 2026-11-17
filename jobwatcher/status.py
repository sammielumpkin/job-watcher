"""data/status.json: describes the latest run."""
import json
from pathlib import Path


def build_status(rows, dates, run_time, results):
    """rows: history rows; dates: sorted raw-file dates; results: this run's per-source results."""
    latest = dates[-1] if dates else ""
    return {
        "run_time": run_time,
        "first_run_date": dates[0] if dates else "",
        "days_with_success": len(dates),
        "open": sum(r["status"] == "open" for r in rows),
        "new_today": sum(r["first_seen"] == latest and not r["first_run"] for r in rows),
        "removed_today": sum(r["removed_date"] == latest for r in rows),
        "sources": [{"name": r["source"], "ok": r["ok"], "count": r["count"]} for r in results],
    }


def write_status(status, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
