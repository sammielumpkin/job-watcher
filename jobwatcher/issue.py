"""Text of the daily GitHub Issue: new and removed postings, each with a link."""
MAX_BODY = 60000  # GitHub's limit is 65,536 characters


def title_for(date):
    return date


def _line(r):
    label = f'{r["employer"]}: {r["title"]}'.replace("[", "(").replace("]", ")")
    loc = f' ({r["location"]})' if r["location"] else ""
    return f'- [{label}]({r["url"]}){loc}'


def _section(heading, rows, budget):
    out = [f"## {heading} ({len(rows)})", ""]
    if not rows:
        out += ["None.", ""]
        return out
    used = 0
    for i, r in enumerate(rows):
        line = _line(r)
        if used + len(line) > budget:
            out += [f"_…and {len(rows) - i} more (list truncated; see data/history.csv)._", ""]
            return out
        out.append(line)
        used += len(line) + 1
    out.append("")
    return out


def build_body(rows, date, sources=None):
    new = sorted((r for r in rows if r["first_seen"] == date and not r["first_run"]),
                 key=lambda r: (r["employer"], r["title"], r["posting_id"]))
    gone = sorted((r for r in rows if r["removed_date"] == date),
                  key=lambda r: (r["employer"], r["title"], r["posting_id"]))
    first = sum(r["first_run"] and r["first_seen"] == date for r in rows)
    lines = [f"Job Watcher report for {date} (UTC).", ""]
    if sources is not None:
        bad = [s["name"] for s in sources if not s["ok"]]
        lines += [f"Sources ok: {len(sources) - len(bad)} of {len(sources)}."
                  + (f" Failed: {', '.join(bad)}." if bad else ""), ""]
    if first:
        lines += [f"{first} postings were first seen today as the starting snapshot of a source "
                  "(first-run postings); they are not listed as new.", ""]
    half = MAX_BODY // 2
    lines += _section("New postings", new, half)
    lines += _section("Removed postings", gone, half)
    return "\n".join(lines).rstrip() + "\n"
