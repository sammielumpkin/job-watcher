from jobwatcher.issue import build_body, title_for

D = "2026-11-17"


def row(pid, employer="Acme", title="Analyst", url=None, **kw):
    r = {"posting_id": pid, "employer": employer, "title": title, "location": "",
         "url": url or f"https://x/{pid}", "first_seen": "2026-11-01", "first_run": False,
         "status": "open", "removed_date": ""}
    r.update(kw)
    return r


def test_title_is_the_date():
    assert title_for(D) == "2026-11-17"


def test_lists_new_and_removed_with_links():
    rows = [row("a:1", title="New One", first_seen=D, location="NYC"),
            row("a:2", title="Gone One", status="removed", removed_date=D),
            row("a:3", title="Old", first_seen="2026-11-01"),
            row("a:4", title="Gone Earlier", status="removed", removed_date="2026-11-10")]
    body = build_body(rows, D)
    new_part, removed_part = body.split("## Removed postings")
    assert "## New postings (1)" in new_part
    assert "[Acme: New One](https://x/a:1) (NYC)" in new_part
    assert "## Removed postings" not in new_part and "[Acme: Gone One](https://x/a:2)" in removed_part
    assert "(1)" in removed_part.splitlines()[0]
    assert "Old" not in body and "Gone Earlier" not in body


def test_first_run_postings_are_not_new():
    rows = [row("a:1", first_seen=D, first_run=True), row("a:2", first_seen=D)]
    body = build_body(rows, D)
    assert "## New postings (1)" in body
    assert "starting snapshot" in body and "1 postings" in body


def test_day_with_no_changes_still_has_a_body():
    body = build_body([row("a:1")], D)
    assert "## New postings (0)" in body and "## Removed postings (0)" in body
    assert body.count("None.") == 2


def test_failed_sources_are_named():
    body = build_body([], D, [{"name": "a", "ok": True, "count": 3}, {"name": "b", "ok": False, "count": 0}])
    assert "Sources ok: 1 of 2. Failed: b." in body


def test_brackets_in_titles_do_not_break_links():
    body = build_body([row("a:1", title="Analyst [Remote]", first_seen=D)], D)
    assert "[Acme: Analyst (Remote)](https://x/a:1)" in body


def test_long_lists_are_truncated_under_github_limit():
    rows = [row(f"a:{i}", title="T" * 200, first_seen=D) for i in range(1000)]
    body = build_body(rows, D)
    assert len(body) < 65000 and "more (list truncated" in body
