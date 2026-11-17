"""Convert each ATS's raw JSON into the common posting columns."""
from datetime import datetime, timezone

COLUMNS = ["posting_id", "source", "source_id", "employer", "title", "location",
           "department", "posted_date", "url", "in_role", "first_run", "first_seen",
           "last_seen", "status", "removed_date"]


def _s(v):
    return "" if v is None else str(v).strip()


def _iso_to_utc_date(v):
    """ISO-8601 timestamp (any offset) -> UTC YYYY-MM-DD, or '' if missing/unparseable."""
    if not v:
        return ""
    try:
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _ms_to_utc_date(v):
    if not v:
        return ""
    try:
        return datetime.fromtimestamp(int(v) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OverflowError, OSError):
        return ""


def _row(source, employer, source_id, title, location, department, posted_date, url):
    return {"source": source, "source_id": _s(source_id), "employer": employer,
            "title": _s(title), "location": _s(location), "department": _s(department),
            "posted_date": posted_date, "url": _s(url)}


def convert_greenhouse(source, employer, raw):
    # The list endpoint has no department field, so department stays empty.
    out = []
    for j in raw["jobs"]:
        loc = j.get("location") or {}
        out.append(_row(source, employer, j["id"], j.get("title"), loc.get("name"), "",
                        _iso_to_utc_date(j.get("first_published")), j.get("absolute_url")))
    return out


def convert_lever(source, employer, raw):
    out = []
    for j in raw:
        cat = j.get("categories") or {}
        out.append(_row(source, employer, j["id"], j.get("text"), cat.get("location"),
                        cat.get("department") or cat.get("team"),
                        _ms_to_utc_date(j.get("createdAt")), j.get("hostedUrl")))
    return out


def convert_ashby(source, employer, raw):
    out = []
    for j in raw["jobs"]:
        out.append(_row(source, employer, j["id"], j.get("title"), j.get("location"),
                        j.get("department"), _iso_to_utc_date(j.get("publishedAt")),
                        j.get("jobUrl")))
    return out


CONVERTERS = {"greenhouse": convert_greenhouse, "lever": convert_lever, "ashby": convert_ashby}


def convert(system, source, employer, raw):
    """Return a list of dicts with source, source_id, employer, title, location,
    department, posted_date, url. Raises KeyError/TypeError on an unexpected shape."""
    return CONVERTERS[system](source, employer, raw)


def count_postings(system, raw):
    return len(raw["jobs"]) if system in ("greenhouse", "ashby") else len(raw)
