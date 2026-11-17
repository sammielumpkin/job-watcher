JW.nav("index.html");
const $ = id => document.getElementById(id);

function list(el, rows, empty) {
  el.innerHTML = rows.length ? rows.map(r =>
    `<li><a href="${JW.esc(r.url)}" target="_blank" rel="noopener">${JW.esc(r.title)}</a>` +
    `<div class="meta">${JW.esc(r.employer)}${r.location ? " &middot; " + JW.esc(r.location) : ""}` +
    `${r.in_role ? " &middot; in role" : ""}</div></li>`).join("")
    : `<li class="muted">${empty}</li>`;
}

JW.loadData().then(d => {
  const s = d.status;
  JW.banner($("banner"), d);
  $("lastrun").textContent = "Last run: " + s.run_time.replace("T", " ").replace("Z", " UTC");
  const cards = [[s.days_with_success, "days with a successful run"], [s.open, "open"],
                 [s.new_today, "new today"], [s.removed_today, "removed today"]];
  $("cards").innerHTML = cards.map(([n, l]) =>
    `<div class="card"><div class="n">${JW.fmt(n)}</div><div class="l">${l}</div></div>`).join("");
  $("sources").innerHTML = s.sources.map(x =>
    `<li><span>${JW.esc(x.name)}</span><span class="${x.ok ? "ok" : "fail"}">` +
    `${x.ok ? "ok &middot; " + JW.fmt(x.count) : "failed"}</span></li>`).join("");

  // First-run postings are left out of "new", as in status.json.
  const fresh = d.rows.filter(r => !r.first_run && r.first_seen === d.runDate);
  const gone = d.rows.filter(r => r.removed_date === d.runDate);
  $("newh").textContent = `New in the latest run (${JW.fmt(fresh.length)})`;
  $("remh").textContent = `Removed in the latest run (${JW.fmt(gone.length)})`;
  list($("newl"), fresh, "No new postings in the latest run.");
  list($("reml"), gone, "No postings were removed in the latest run.");
}).catch(e => { JW.banner($("banner"), null, e); $("lastrun").textContent = ""; });
