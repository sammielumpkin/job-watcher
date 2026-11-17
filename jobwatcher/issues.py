"""Open (or update) today's GitHub Issue and close earlier days' issues, using the gh CLI."""
import csv
import json
import re
import subprocess
import sys

from .issue import build_body, title_for
from .sources import ROOT

DATE_TITLE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def plan(existing, date):
    """existing: [{number, title, state}] (state OPEN/CLOSED). Returns (today_issue_or_None,
    numbers_to_close): every open issue titled with an earlier date is closed."""
    today = next((i for i in existing if i["title"] == title_for(date)), None)
    stale = [i["number"] for i in existing
             if i["state"].upper() == "OPEN" and DATE_TITLE.match(i["title"]) and i["title"] < date]
    return today, stale


def gh(*args, check=True):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=check, encoding="utf-8")


def load_rows():
    with open(ROOT / "data" / "history.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["first_run"] = r["first_run"] == "true"
        r["in_role"] = r["in_role"] == "true"
    return rows


def main(dry_run=False):
    status = json.loads((ROOT / "data" / "status.json").read_text(encoding="utf-8"))
    date = status["run_time"][:10]
    body = build_body(load_rows(), date, status["sources"])
    if dry_run:
        print(title_for(date), "\n", body)
        return
    listing = json.loads(gh("issue", "list", "--state", "all", "--limit", "200",
                            "--json", "number,title,state").stdout)
    today, stale = plan(listing, date)
    if today is None:
        gh("issue", "create", "--title", title_for(date), "--body", body)
    else:  # second run on the same day: update that day's issue
        gh("issue", "edit", str(today["number"]), "--body", body)
        if today["state"].upper() != "OPEN":
            gh("issue", "reopen", str(today["number"]))
    for n in stale:
        gh("issue", "close", str(n), "--comment", f"Superseded by the {date} report.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
