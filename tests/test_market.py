from jobwatcher.market import compute


def row(pid, first_seen, removed=None, first_run=False, in_role=False, employer="A", location="NYC"):
    return {"posting_id": pid, "employer": employer, "location": location, "first_run": str(first_run).lower(),
            "in_role": str(in_role).lower(), "first_seen": first_seen, "removed_date": removed or "",
            "status": "removed" if removed else "open"}


def test_definitions():
    rows = [
        row("a", "2026-01-01", first_run=True),                      # baseline: excluded from new/days/share
        row("b", "2026-01-02", removed="2026-01-05", in_role=True),  # 3 days
        row("c", "2026-01-02", removed="2026-01-12"),                # 10 days
        row("d", "2026-01-09", employer="B", location="SF"),         # too recent for the 7-day share
        row("e", "2026-01-10", first_run=True, removed="2026-01-11"),  # removed, but not counted in spans
    ]
    m = compute(rows, "2026-01-10")
    assert m["new_per_day_all"] == {"2026-01-02": 2, "2026-01-09": 1}
    assert m["new_per_day_role"] == {"2026-01-02": 1}
    assert m["removed_per_day"] == {"2026-01-05": 1, "2026-01-11": 1, "2026-01-12": 1}
    assert m["open_total"] == 2 and m["top_employer"] == "A"
    assert m["median_days_open"] == 6.5 and m["days_open_n"] == 2
    assert (m["share_eligible"], m["share_n"], m["share_within_7"]) == (2, 1, 50.0)
    assert m["top_locations"] == [("NYC", 1), ("SF", 1)]


def test_empty_cases():
    m = compute([row("a", "2026-01-01", first_run=True)], "2026-01-01")
    assert m["median_days_open"] is None and m["share_within_7"] is None
    assert m["new_latest_all"] == 0
