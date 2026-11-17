# Job Watcher

[![tests](https://github.com/sammielumpkin/job-watcher/actions/workflows/tests.yml/badge.svg)](https://github.com/sammielumpkin/job-watcher/actions/workflows/tests.yml)

Every day GitHub Actions pulls the open postings at 27 fintech employers, compares them with
what it saw before, records what is new and what is gone, opens a GitHub Issue for the day, and
publishes the result as a website.

**Live site:** https://sammielumpkin.github.io/job-watcher/

Role watched: **financial analyst / FP&A**. All postings the boards return are kept; the ones in
my role are marked `in_role`.

## Build the history from the raw files

```
python -m jobwatcher.history
```

This reads only `data/raw/<date>/<source>.json.gz` and rewrites `data/history.csv`. Running it
again gives the same file, and a change to a rule (for example the title rule) applies to every
day of the history. The full daily run (fetch, history, status) is `python -m jobwatcher.run`.

Tests: `pip install -r requirements-dev.txt` then `python -m pytest -q`.
Market cross-check: `python -m jobwatcher.market` prints the six Market numbers from
`history.csv` so they can be compared with `market.html`.

## Sources

Each board is read as JSON with no login. No board comes near 5,000 postings (the largest,
Stripe, has about 790), so no search term is used.

| Employer | Applicant tracking system | Source name |
|---|---|---|
| Stripe | Greenhouse | stripe |
| Robinhood | Greenhouse | robinhood |
| Coinbase | Greenhouse | coinbase |
| SoFi | Greenhouse | sofi |
| Affirm | Greenhouse | affirm |
| Chime | Greenhouse | chime |
| Brex | Greenhouse | brex |
| Toast | Greenhouse | toast |
| Plaid | Ashby | plaid |
| Ramp | Ashby | ramp |
| Mercury | Greenhouse | mercury |
| Block | Greenhouse | block |
| Carta | Greenhouse | carta |
| Gusto | Greenhouse | gusto |
| Betterment | Greenhouse | betterment |
| Upstart | Greenhouse | upstart |
| Adyen | Greenhouse | adyen |
| Bill.com | Greenhouse | billcom |
| Airwallex | Ashby | airwallex |
| Monzo | Greenhouse | monzo |
| Payoneer | Greenhouse | payoneer |
| Jane Street | Greenhouse | janestreet |
| Point72 | Greenhouse | point72 |
| Ripple | Greenhouse | ripple |
| Wealthfront | Lever | wealthfront |
| Anchorage | Lever | anchorage |
| Nubank | Ashby | nubank |

## Title rule

A posting is `in_role` when its **title** matches at least one include pattern and none of the
exclude patterns (case-insensitive; only the title is looked at). Defined in `jobwatcher/rule.py`.

- **Include:** FP&A / FPA, financial planning, finance or financial analyst / associate /
  modeler, finance manager / partner / business partner / specialist, finance & strategy,
  strategic / corporate / commercial / business / product finance, finance forecasting,
  forecasting, budget / budgeting, financial reporting / control, controllership,
  treasury analyst.
- **Exclude:** engineer, developer, software, designer, scientist, researcher, counsel, lawyer,
  legal, sales, account executive, recruit, talent, marketing, product manager / director /
  lead / operations, compliance, fraud, financial crimes, AML, KYC, risk, system(s), Workday,
  Oracle, ERP, customer, support, trader, quant, partnership(s), internal audit, tax,
  head of, chief, VP, vice president.

## Files

| File | What it does |
|---|---|
| `index.html` | Today page: time of the last run, status of every source, the four counts, new and removed postings of the latest run |
| `browse.html` | Browse page: open postings, in-role/all switch, filters, title search, sort, apply links, starred shortlist |
| `market.html` | Market page: six sections, each with a finding heading, a paragraph and a chart, all computed in the browser |
| `assets/site.css` | Fonts and colors shared by the three pages |
| `assets/site.js` | Shared navigation bar, CSV/data loading, chart helpers, service-worker registration |
| `assets/today.js`, `assets/browse.js`, `assets/market.js` | Page logic for each page |
| `manifest.webmanifest`, `sw.js`, `icons/` | Make the site installable; the service worker loads data from the network when online and from its cache when offline |
| `tools/make_icons.py` | Writes the PNG icons in `icons/` |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are |
| `jobwatcher/run.py` | One daily run: fetch, build history, write status and run log |
| `jobwatcher/fetch.py` | Calls each source, retries, saves compressed raw files, records success or failure |
| `jobwatcher/convert.py` | Converts each system's JSON into the common columns |
| `jobwatcher/history.py` | Builds `data/history.csv` from the raw files (first-seen, last-seen, removed, reopened) |
| `jobwatcher/rule.py` | The title rule |
| `jobwatcher/status.py` | Builds `data/status.json` |
| `jobwatcher/sources.py` | Loads `sources.json` |
| `jobwatcher/issue.py` | Builds the text of the daily Issue |
| `jobwatcher/issues.py` | Opens or updates today's Issue and closes earlier ones, using the `gh` CLI |
| `jobwatcher/market.py` | Python check that computes the six Market numbers from `history.csv` |
| `sources.json` | The 27 sources: name, system, slug, URL |
| `probe.py`, `make_config.py`, `probe_results.json` | One-time tools that tested which employers have a readable board and wrote `sources.json` |
| `tests/` | pytest suite: conversion for each system, title rule, first-seen / last-seen / removed logic, status, Issue text and planning, Market numbers |
| `.github/workflows/daily.yml` | Daily run at 06:23 UTC (and manual trigger): pipeline, Issue, commit data |
| `.github/workflows/tests.yml` | Runs pytest on every push |
| `requirements-dev.txt` | Test dependency (pytest) |
| `data/raw/<date>/<source>.json.gz` | What each source returned, compressed |
| `data/history.csv` | One row per posting, built from the raw files |
| `data/status.json` | Describes the latest run |
| `data/run_log.json` | Per-day, per-source outcome of each run (see below) |

## Choices the brief does not spell out

- **Source names.** A source's name (used in file names, `posting_id` and `status.json`) is the
  board's lowercase slug, for example `billcom` for Bill.com and `janestreet` for Jane Street.
  `employer` in the history keeps the display name. A `posting_id` is `<source>:<source_id>`.
- **An empty board counts as a failure.** A board that returns zero postings is treated as
  failed (after two retries) and writes no raw file. An empty answer is more likely a glitch than a
  real empty board, and counting it as success would mark every posting at that employer removed.
- **Department is empty for Greenhouse.** Greenhouse's list endpoint has no department field, so
  `department` is left empty for those sources. Lever and Ashby provide it. Posted date comes from
  `first_published` (Greenhouse), `createdAt` (Lever) and `publishedAt` (Ashby), as UTC dates.
- **`data/run_log.json`.** An extra file, not required by the brief. It keeps, for every run day,
  the run time and each source's result including the error text of failures, because
  `status.json` only describes the latest run. A second run on the same day replaces that day's
  entry.
- **Market page.** Postings with no location are not ranked in the top locations. Removed postings
  per day counts every posting with a removed date, including first-run ones. "Last run" is the
  UTC date in `status.json`'s `run_time`.
- **Browse page.** "Days open" is the last run date minus the first-seen date, so first-run
  postings show the time since watching began, not since they were posted. A "shortlist only"
  checkbox is added.
- **Pages.** The site is served from the repository root on the `main` branch, so the pages
  reach the data at `data/history.csv` and `data/status.json`.
