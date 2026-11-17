import csv
import gzip
import json

from jobwatcher.history import build_history, raw_dates, write_history
from jobwatcher.convert import COLUMNS

A = {"source": "a", "name": "A Co", "system": "ashby", "url": ""}
B = {"source": "b", "name": "B Co", "system": "lever", "url": ""}
role = lambda t: "analyst" in t.lower()


def put(tmp, date, source, ids, system="ashby"):
    d = tmp / date
    d.mkdir(parents=True, exist_ok=True)
    if system == "ashby":
        raw = {"jobs": [{"id": i, "title": f"{i} Analyst" if i != "x" else "Chef", "jobUrl": f"u/{i}"} for i in ids]}
    else:
        raw = [{"id": i, "text": f"{i} Analyst", "hostedUrl": f"u/{i}"} for i in ids]
    (d / f"{source}.json.gz").write_bytes(gzip.compress(json.dumps(raw).encode()))


def get(rows, pid):
    return next(r for r in rows if r["posting_id"] == pid)


def test_first_seen_last_seen_and_first_run(tmp_path):
    put(tmp_path, "2026-11-01", "a", ["1", "2"])
    put(tmp_path, "2026-11-02", "a", ["1", "2", "3"])
    put(tmp_path, "2026-11-03", "a", ["1", "2", "3"])
    rows = build_history(tmp_path, [A], role)
    r1, r3 = get(rows, "a:1"), get(rows, "a:3")
    assert (r1["first_seen"], r1["last_seen"], r1["first_run"]) == ("2026-11-01", "2026-11-03", True)
    assert (r3["first_seen"], r3["last_seen"], r3["first_run"]) == ("2026-11-02", "2026-11-03", False)
    assert r1["status"] == "open" and r1["removed_date"] == ""


def test_removed_when_source_has_file_and_no_longer_lists(tmp_path):
    put(tmp_path, "2026-11-01", "a", ["1", "2"])
    put(tmp_path, "2026-11-02", "a", ["1"])
    rows = build_history(tmp_path, [A], role)
    r2 = get(rows, "a:2")
    assert (r2["status"], r2["removed_date"], r2["last_seen"]) == ("removed", "2026-11-02", "2026-11-01")
    assert get(rows, "a:1")["status"] == "open"


def test_failed_source_day_removes_nothing(tmp_path):
    put(tmp_path, "2026-11-01", "a", ["1"])
    put(tmp_path, "2026-11-01", "b", ["9"], "lever")
    put(tmp_path, "2026-11-02", "b", ["9"], "lever")  # source a has no file on day 2 (failed)
    rows = build_history(tmp_path, [A, B], role)
    assert get(rows, "a:1")["status"] == "open"
    assert get(rows, "a:1")["last_seen"] == "2026-11-01"


def test_relisted_posting_reopens_and_keeps_first_seen(tmp_path):
    put(tmp_path, "2026-11-01", "a", ["1", "2"])
    put(tmp_path, "2026-11-02", "a", ["1"])
    put(tmp_path, "2026-11-04", "a", ["1", "2"])
    r2 = get(build_history(tmp_path, [A], role), "a:2")
    assert (r2["status"], r2["removed_date"], r2["first_seen"], r2["last_seen"]) == \
        ("open", "", "2026-11-01", "2026-11-04")


def test_first_run_is_per_source(tmp_path):
    put(tmp_path, "2026-11-01", "a", ["1"])
    put(tmp_path, "2026-11-02", "a", ["1"])
    put(tmp_path, "2026-11-02", "b", ["9"], "lever")  # b's first file is day 2
    rows = build_history(tmp_path, [A, B], role)
    assert get(rows, "b:9")["first_run"] is True
    assert get(rows, "b:9")["first_seen"] == "2026-11-02"


def test_in_role_and_keeps_every_posting(tmp_path):
    put(tmp_path, "2026-11-01", "a", ["1", "x"])
    rows = build_history(tmp_path, [A], role)
    assert get(rows, "a:1")["in_role"] is True
    assert get(rows, "a:x")["in_role"] is False  # kept, just not in role
    assert len(rows) == 2


def test_rows_sorted_and_build_is_reproducible(tmp_path):
    put(tmp_path, "2026-11-01", "b", ["2", "1"], "lever")
    put(tmp_path, "2026-11-01", "a", ["3"])
    put(tmp_path, "2026-11-02", "a", ["3", "4"])
    r1 = build_history(tmp_path, [A, B], role)
    r2 = build_history(tmp_path, [B, A], role)
    assert r1 == r2
    ids = [r["posting_id"] for r in r1]
    assert ids == sorted(ids)
    out = tmp_path / "h.csv"
    write_history(r1, out)
    with open(out, newline="") as f:
        read = list(csv.DictReader(f))
    assert list(read[0]) == COLUMNS
    assert read[0]["first_run"] in ("true", "false") and read[0]["in_role"] in ("true", "false")


def test_raw_dates_ignores_empty_folders(tmp_path):
    put(tmp_path, "2026-11-01", "a", ["1"])
    (tmp_path / "2026-11-02").mkdir()
    assert raw_dates(tmp_path) == ["2026-11-01"]
