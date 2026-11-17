JW.nav("market.html");
const $ = id => document.getElementById(id);
const f = JW.fmt;
const pl = (n, w) => `${f(n)} ${w}${n === 1 ? "" : "s"}`;

// Every number on this page is computed here from data/history.csv (rows) and the date of the
// latest run. jobwatcher/market.py computes the same numbers in Python as a cross-check.
function compute(rows, runDate) {
  const byDay = (list, key) => {
    const m = new Map();
    for (const r of list) m.set(r[key], (m.get(r[key]) || 0) + 1);
    return m;
  };
  const top = (m, n) => [...m].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1)).slice(0, n);

  // 1. New per day: first_seen, first-run postings left out. All postings and in-role postings.
  const fresh = rows.filter(r => !r.first_run);
  const newAll = byDay(fresh, "first_seen");
  const newRole = byDay(fresh.filter(r => r.in_role), "first_seen");

  // 2. Removed per day: every posting with a removed date.
  const removed = rows.filter(r => r.removed_date);
  const remDay = byDay(removed, "removed_date");

  // 3. Open per employer, as of the last run.
  const open = rows.filter(r => r.status === "open");
  const emp = [...byDay(open, "employer")].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));

  // 4. Days open: removed, not first-run.
  const spans = removed.filter(r => !r.first_run).map(r => JW.days(r.first_seen, r.removed_date));

  // 5. Share removed within seven days: not first-run, first seen at least 7 days before last run.
  const elig = fresh.filter(r => JW.days(r.first_seen, runDate) >= 7);
  const quick = elig.filter(r => r.removed_date && JW.days(r.first_seen, r.removed_date) <= 7).length;

  // 6. Top locations among open postings (blank locations are not ranked).
  const locs = top(byDay(open.filter(r => r.location), "location"), 10);

  const allDays = rows.map(r => r.first_seen).concat(removed.map(r => r.removed_date), [runDate]).sort();
  return {
    runDate, firstDate: allDays[0], newAll, newRole, remDay, emp, openTotal: open.length,
    spans, medianDays: JW.median(spans), elig: elig.length, quick,
    share: elig.length ? quick / elig.length : null, locs,
    removedTotal: removed.length, newAllTotal: fresh.length,
    newRoleTotal: fresh.filter(r => r.in_role).length
  };
}

function dayRange(a, b) {
  const out = [];
  for (let t = Date.parse(a); t <= Date.parse(b); t += 864e5) out.push(new Date(t).toISOString().slice(0, 10));
  return out;
}

function section(n, head, text, stat, chartHtml) {
  return `<section class="sec panel" id="s${n}"><h2><span class="no">${n})</span> <span>${JW.esc(head)}</span></h2><p>${JW.esc(text)}</p>` +
    `<p class="stat">${stat}</p>${chartHtml}</section>`;
}
const chartBox = (id, label) => `<div class="chart" id="${id}" role="group" aria-label="${JW.esc(label)}"></div>`;

function render(d) {
  const m = compute(d.rows, d.runDate);
  const range = dayRange(m.firstDate, m.runDate);
  const lastNew = m.newAll.get(m.runDate) || 0, lastNewRole = m.newRole.get(m.runDate) || 0;
  const lastRem = m.remDay.get(m.runDate) || 0;
  const nDays = range.length;
  const out = [];

  // 1 New postings per day
  out.push(section(1,
    m.newAllTotal === 0 ? "No new postings yet: the first run is the baseline"
      : `${pl(lastNew, "new posting")} in the latest run, ${f(lastNewRole)} in my role`,
    m.newAllTotal === 0
      ? `Postings already open on ${m.firstDate}, when the tool began watching, have no known start date and are left out, so new postings start counting from the second run.`
      : `Counts postings by the day they were first seen, leaving out first-run postings that were already open when watching began. Over ${pl(nDays, "day")} that is ${f(m.newAllTotal)} new postings, ${f(m.newRoleTotal)} of them in my role.`,
    `<b data-k="new_latest_all">${f(lastNew)}</b> new in latest run (all) &middot; <b data-k="new_latest_role">${f(lastNewRole)}</b> (in role)`,
    `<h3>All postings</h3>${chartBox("c1a", "New postings per day, all")}<h3>In my role</h3>${chartBox("c1b", "New postings per day, in role")}` +
    JW.table(["Day", "All", "In role"], range.map(x => [x, m.newAll.get(x) || 0, m.newRole.get(x) || 0]))));

  // 2 Removed per day
  out.push(section(2,
    lastRem === 0 ? "No postings were removed in the latest run" : `${pl(lastRem, "posting")} removed in the latest run`,
    `Counts postings by the day their source stopped listing them. In total ${pl(m.removedTotal, "posting")} ${m.removedTotal === 1 ? "has" : "have"} been removed since ${m.firstDate}.`,
    `<b data-k="removed_latest">${f(lastRem)}</b> removed in latest run &middot; <b data-k="removed_total">${f(m.removedTotal)}</b> in total`,
    chartBox("c2", "Removed postings per day") +
    JW.table(["Day", "Removed"], range.map(x => [x, m.remDay.get(x) || 0]))));

  // 3 Open per employer
  const e0 = m.emp[0];
  out.push(section(3,
    e0 ? `${e0[0]} has the most open postings (${f(e0[1])} of ${f(m.openTotal)})` : "No open postings",
    `Open postings per employer as of the last run on ${m.runDate}, all roles. ${pl(m.emp.length, "employer")} currently ${m.emp.length === 1 ? "has" : "have"} at least one open posting.`,
    `<b data-k="open_total">${f(m.openTotal)}</b> open &middot; top employer <b data-k="top_employer">${JW.esc(e0 ? e0[0] : "-")}</b> (<b data-k="top_employer_open">${f(e0 ? e0[1] : 0)}</b>)`,
    chartBox("c3", "Open postings per employer")));

  // 4 Days open
  const md = m.medianDays;
  out.push(section(4,
    md === null ? "No removed postings yet, so there is no days-open figure"
      : `Removed postings were open a median of ${f(md)} ${md === 1 ? "day" : "days"}`,
    md === null
      ? "Days open is the removed date minus the first-seen date for removed postings that are not first-run. None exist yet."
      : `Days open is the removed date minus the first-seen date, for ${pl(m.spans.length, "removed posting")} that were not already open when watching began. The median is the middle value, so a few long-lived postings do not skew it.`,
    `median <b data-k="median_days_open">${md === null ? "n/a" : f(md)}</b>${md === null ? "" : " days"} &middot; n = <b data-k="days_open_n">${f(m.spans.length)}</b>`,
    chartBox("c4", "Distribution of days open")));

  // 5 Share within seven days
  const sh = m.share, pct = sh === null ? null : Math.round(sh * 1000) / 10;
  out.push(section(5,
    sh === null ? "Too early to tell how quickly postings are removed"
      : `${pct}% of postings were removed within seven days`,
    sh === null
      ? "This share needs postings that are not first-run and were first seen at least seven days before the last run. There are none yet."
      : `Among ${pl(m.elig, "posting")} first seen at least seven days before the last run (first-run postings excluded), ${f(m.quick)} had a removed date seven days or less after the first-seen date.`,
    `share <b data-k="share_within_7">${pct === null ? "n/a" : pct + "%"}</b> &middot; <b data-k="share_n">${f(m.quick)}</b> of <b data-k="share_eligible">${f(m.elig)}</b>`,
    sh === null ? "" : `<div class="stack" role="img" aria-label="${pct}% removed within seven days">` +
      `<div class="a" style="flex:${Math.max(m.quick, 0.0001)}">Removed within 7 days: ${f(m.quick)}</div>` +
      `<div class="b" style="flex:${Math.max(m.elig - m.quick, 0.0001)}">Not removed within 7 days: ${f(m.elig - m.quick)}</div></div>`));

  // 6 Top locations
  const l0 = m.locs[0];
  out.push(section(6,
    l0 ? `${l0[0]} leads open postings with ${f(l0[1])}` : "No open postings with a location",
    `The ten most common locations among open postings as of ${m.runDate}, as written by each employer's board (so "New York" and "New York, NY" count separately). Postings without a location are not ranked.`,
    `top location <b data-k="top_location">${JW.esc(l0 ? l0[0] : "-")}</b> (<b data-k="top_location_open">${f(l0 ? l0[1] : 0)}</b>)`,
    chartBox("c6", "Top locations among open postings")));

  $("intro").textContent = `Computed in your browser from data/history.csv, as of the last run on ${m.runDate}. ` +
    `Postings that were already open when watching began (first run) are left out where noted.`;
  $("sections").innerHTML = out.join("");

  const cols = (id, map, label) => JW.columns($(id), range.map(x => ({ label: x.slice(5), value: map.get(x) || 0, tip: `${x}: ${f(map.get(x) || 0)}` })), label);
  if ($("c1a")) { cols("c1a", m.newAll, "New postings per day, all"); cols("c1b", m.newRole, "New postings per day, in role"); }
  cols("c2", m.remDay, "Removed postings per day");
  JW.hbars($("c3"), m.emp.map(([label, value]) => ({ label, value })));
  const buckets = [["0", 0, 0], ["1", 1, 1], ["2", 2, 2], ["3", 3, 3], ["4", 4, 4], ["5", 5, 5], ["6", 6, 6], ["7", 7, 7],
                   ["8-14", 8, 14], ["15-30", 15, 30], ["31+", 31, Infinity]];
  JW.columns($("c4"), buckets.map(([label, lo, hi]) => {
    const v = m.spans.filter(x => x >= lo && x <= hi).length;
    return { label, value: v, tip: `${label} days open: ${f(v)}` };
  }), "Distribution of days open");
  JW.hbars($("c6"), m.locs.map(([label, value]) => ({ label, value })));
  window.JW_MARKET = m;
}

JW.loadData().then(d => { JW.banner($("banner"), d); render(d); })
  .catch(e => { JW.banner($("banner"), null, e); $("intro").textContent = ""; });
