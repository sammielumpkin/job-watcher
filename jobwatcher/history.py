"""Build data/history.csv from the raw files alone (deterministic, rerunnable)."""
import csv
import gzip
import json
from pathlib import Path

from .convert import COLUMNS, convert
from .sources import load_sources


def raw_dates(raw_dir):
    """Sorted dates that have at least one raw file."""
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        return []
    return sorted(d.name for d in raw_dir.iterdir() if d.is_dir() and any(d.glob("*.json.gz")))


def read_raw(raw_dir, date, source):
    p = Path(raw_dir) / date / f"{source}.json.gz"
    return json.loads(gzip.decompress(p.read_bytes())) if p.exists() else None


def build_history(raw_dir, sources, is_role):
    """Walk the raw files day by day and return history rows sorted by posting_id.

    - first sight of a posting: first_seen = that day; first_run if it is in its source's first raw file
    - every posting a source lists that day: last_seen = that day, status open, removed_date cleared
    - an open posting whose source has a raw file that day but no longer lists it: removed that day
    - days on which a source has no raw file (it failed) change nothing for that source
    """
    by_source = {s["source"]: s for s in sources}
    dates = raw_dates(raw_dir)
    first_date = {}
    rows = {}
    for date in dates:
        for key, src in by_source.items():
            raw = read_raw(raw_dir, date, key)
            if raw is None:
                continue
            first_date.setdefault(key, date)
            listed = {}
            for p in convert(src["system"], key, src["name"], raw):
                listed[p["source_id"]] = p  # a repeated id in one file counts once
            for sid, p in listed.items():
                pid = f"{key}:{sid}"
                row = rows.get(pid)
                if row is None:
                    row = rows[pid] = {"posting_id": pid, "first_run": first_date[key] == date,
                                       "first_seen": date}
                row.update(p)
                row["in_role"] = is_role(p["title"])
                row.update(last_seen=date, status="open", removed_date="")
            for pid, row in rows.items():
                if row["source"] == key and row["status"] == "open" and row["source_id"] not in listed:
                    row.update(status="removed", removed_date=date)
    return [rows[k] for k in sorted(rows)]


def _cell(v):
    return ("true" if v else "false") if isinstance(v, bool) else v


def write_history(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUMNS)
        for r in rows:
            w.writerow([_cell(r[c]) for c in COLUMNS])


def build(raw_dir, out_path, sources=None, is_role=None):
    from .rule import in_role
    rows = build_history(raw_dir, sources or load_sources(), is_role or in_role)
    write_history(rows, out_path)
    return rows


if __name__ == "__main__":
    from .sources import ROOT
    rows = build(ROOT / "data" / "raw", ROOT / "data" / "history.csv")
    print(f"wrote {len(rows)} rows to data/history.csv")
