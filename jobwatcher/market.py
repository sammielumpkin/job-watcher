"""Cross-check for the Market page: compute its six numbers from data/history.csv.

Run:  python -m jobwatcher.market            (reads data/history.csv and data/status.json)
Compare the printed values with the bold numbers under each heading on market.html.
Definitions follow the project brief; first_run postings are left out where it says so.
"""
import csv
import json
import statistics
import sys
from collections import Counter
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def _days(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def compute(rows, run_date):
    """rows: dicts as read by csv.DictReader. run_date: YYYY-MM-DD of the latest run."""
    first_run = lambda r: r["first_run"] == "true"
    fresh = [r for r in rows if not first_run(r)]
    removed = [r for r in rows if r["removed_date"]]
    open_ = [r for r in rows if r["status"] == "open"]

    # 1. New per day (first-run left out), all and in role.
    new_all = Counter(r["first_seen"] for r in fresh)
    new_role = Counter(r["first_seen"] for r in fresh if r["in_role"] == "true")
    # 2. Removed per day.
    rem = Counter(r["removed_date"] for r in removed)
    # 3. Open per employer.
    emp = sorted(Counter(r["employer"] for r in open_).items(), key=lambda kv: (-kv[1], kv[0]))
    # 4. Days open: removed, not first-run; median.
    spans = [_days(r["first_seen"], r["removed_date"]) for r in removed if not first_run(r)]
    # 5. Share removed within seven days.
    elig = [r for r in fresh if _days(r["first_seen"], run_date) >= 7]
    quick = [r for r in elig if r["removed_date"] and _days(r["first_seen"], r["removed_date"]) <= 7]
    # 6. Top locations among open postings (blank locations not ranked).
    locs = sorted(Counter(r["location"] for r in open_ if r["location"]).items(),
                  key=lambda kv: (-kv[1], kv[0]))[:10]
    return {
        "run_date": run_date,
        "new_per_day_all": dict(sorted(new_all.items())),
        "new_per_day_role": dict(sorted(new_role.items())),
        "new_latest_all": new_all.get(run_date, 0),
        "new_latest_role": new_role.get(run_date, 0),
        "removed_per_day": dict(sorted(rem.items())),
        "removed_latest": rem.get(run_date, 0),
        "removed_total": len(removed),
        "open_total": len(open_),
        "open_per_employer": emp,
        "top_employer": emp[0][0] if emp else None,
        "top_employer_open": emp[0][1] if emp else 0,
        "median_days_open": statistics.median(spans) if spans else None,
        "days_open_n": len(spans),
        "share_eligible": len(elig),
        "share_n": len(quick),
        "share_within_7": round(100 * len(quick) / len(elig), 1) if elig else None,
        "top_locations": locs,
        "top_location": locs[0][0] if locs else None,
        "top_location_open": locs[0][1] if locs else 0,
    }


def load(data_dir=DATA):
    with open(Path(data_dir) / "history.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    status = json.loads((Path(data_dir) / "status.json").read_text(encoding="utf-8"))
    return rows, status["run_time"][:10]


def main():
    m = compute(*load())
    print(f"Market numbers as of the last run, {m['run_date']}\n")
    print(f"1. New in latest run:      all {m['new_latest_all']}, in role {m['new_latest_role']}")
    print(f"2. Removed in latest run:  {m['removed_latest']} (total removed {m['removed_total']})")
    print(f"3. Open postings:          {m['open_total']}; top employer "
          f"{m['top_employer']} ({m['top_employer_open']})")
    print(f"4. Median days open:       {m['median_days_open']} (n = {m['days_open_n']})")
    sh = m["share_within_7"]
    print(f"5. Removed within 7 days:  {'n/a' if sh is None else str(sh) + '%'} "
          f"({m['share_n']} of {m['share_eligible']})")
    print(f"6. Top location:           {m['top_location']} ({m['top_location_open']})")
    if "--full" in sys.argv:
        print(json.dumps(m, indent=1))


if __name__ == "__main__":
    main()
