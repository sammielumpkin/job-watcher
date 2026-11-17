from jobwatcher.issues import plan

I = lambda n, t, s="OPEN": {"number": n, "title": t, "state": s}


def test_new_day_has_no_issue_and_closes_previous():
    today, stale = plan([I(1, "2026-11-15", "CLOSED"), I(2, "2026-11-16")], "2026-11-17")
    assert today is None and stale == [2]


def test_same_day_rerun_finds_existing_issue_and_does_not_close_it():
    today, stale = plan([I(3, "2026-11-17"), I(2, "2026-11-16")], "2026-11-17")
    assert today["number"] == 3 and stale == [2]


def test_ignores_non_date_issues_and_later_dates():
    _, stale = plan([I(5, "Question about data"), I(6, "2026-11-20")], "2026-11-17")
    assert stale == []
