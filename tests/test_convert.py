from jobwatcher.convert import convert, count_postings


def test_greenhouse():
    raw = {"jobs": [{"id": 8172508, "title": " Abuse Investigator ", "location": {"name": "Dublin"},
                     "first_published": "2026-09-03T23:32:53-04:00",
                     "absolute_url": "https://stripe.com/jobs/search?gh_jid=8172508"}]}
    [r] = convert("greenhouse", "stripe", "Stripe", raw)
    assert r == {"source": "stripe", "source_id": "8172508", "employer": "Stripe",
                 "title": "Abuse Investigator", "location": "Dublin", "department": "",
                 "posted_date": "2026-09-04",  # 23:32 at -04:00 is the next UTC day
                 "url": "https://stripe.com/jobs/search?gh_jid=8172508"}
    assert count_postings("greenhouse", raw) == 1


def test_greenhouse_missing_optional_fields():
    [r] = convert("greenhouse", "x", "X", {"jobs": [{"id": 1, "title": "T", "location": None,
                                                     "absolute_url": "u"}]})
    assert r["location"] == "" and r["posted_date"] == ""


def test_lever():
    raw = [{"id": "abc", "text": "FP&A Analyst", "hostedUrl": "https://jobs.lever.co/x/abc",
            "createdAt": 1788000000000,
            "categories": {"location": "SF", "department": "Finance", "team": "FP&A"}}]
    [r] = convert("lever", "x", "X", raw)
    assert r["source_id"] == "abc" and r["title"] == "FP&A Analyst"
    assert r["location"] == "SF" and r["department"] == "Finance"
    assert r["posted_date"] == "2026-08-29"
    assert r["url"] == "https://jobs.lever.co/x/abc"
    assert count_postings("lever", raw) == 1


def test_lever_department_falls_back_to_team():
    [r] = convert("lever", "x", "X", [{"id": "1", "text": "T", "categories": {"team": "Ops"}}])
    assert r["department"] == "Ops" and r["posted_date"] == ""


def test_ashby():
    raw = {"jobs": [{"id": "u-1", "title": "Data Analyst", "department": "Finance",
                     "location": "Remote", "publishedAt": "2026-06-03T18:24:47.526+00:00",
                     "jobUrl": "https://jobs.ashbyhq.com/plaid/u-1"}]}
    [r] = convert("ashby", "plaid", "Plaid", raw)
    assert r == {"source": "plaid", "source_id": "u-1", "employer": "Plaid",
                 "title": "Data Analyst", "location": "Remote", "department": "Finance",
                 "posted_date": "2026-06-03", "url": "https://jobs.ashbyhq.com/plaid/u-1"}
    assert count_postings("ashby", raw) == 1
