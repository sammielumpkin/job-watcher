from jobwatcher.status import build_status

R = lambda **k: {"status": "open", "first_seen": "2026-11-01", "first_run": False, "removed_date": "", **k}


def test_counts_follow_the_brief():
    rows = [R(first_run=True),                                   # open, first-run
            R(first_seen="2026-11-03"),                          # new today
            R(first_seen="2026-11-03", first_run=True),          # first-run: not new
            R(status="removed", removed_date="2026-11-03"),      # removed today
            R(status="removed", removed_date="2026-11-02")]      # removed earlier
    results = [{"source": "a", "name": "A", "ok": True, "count": 5, "error": ""},
               {"source": "b", "name": "B", "ok": False, "count": 0, "error": "x"}]
    s = build_status(rows, ["2026-11-01", "2026-11-03"], "2026-11-03T06:00:00Z", results)
    assert s == {"run_time": "2026-11-03T06:00:00Z", "first_run_date": "2026-11-01",
                 "days_with_success": 2, "open": 3, "new_today": 1, "removed_today": 1,
                 "sources": [{"name": "a", "ok": True, "count": 5}, {"name": "b", "ok": False, "count": 0}]}
