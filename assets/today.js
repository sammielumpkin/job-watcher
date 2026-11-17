JW.nav("index.html");
const $ = id => document.getElementById(id);

function list(el, rows, empty) {
  el.innerHTML = rows.length ? rows.map(r =>
    `<li><a href="${JW.esc(r.url)}" target="_blank" rel="noopener">${JW.esc(r.title)}</a>` +
    `${r.in_role ? ' <span class="tag">in role</span>' : ""}` +
    `<div class="meta">${JW.esc(r.employer)}${r.location ? " &middot; " + JW.esc(r.location) : ""}</div></li>`).join("")
    : `<li class="muted">${empty}</li>`;
}

JW.loadData().then(d => {
  const s = d.status;
  JW.banner($("banner"), d);
  $("lastrun").textContent = "Last run: " + s.run_time.replace("T", " ").replace("Z", " UTC");
  const cards = [[s.days_with_success, "Days with a successful run"], [s.open, "Open"],
                 [s.new_today, "New today"], [s.removed_today, "Removed today"]];
  $("cards").innerHTML = cards.map(([n, l]) =>
    `<div class="card"><div class="l">${l}</div><div class="n">${JW.fmt(n)}</div></div>`).join("");
  $("sources").innerHTML = s.sources.map(x =>
    `<li class="${x.ok ? "" : "bad"}"><span class="dot"></span><span class="nm">${JW.esc(x.name)}</span>` +
    `<span class="ct ${x.ok ? "ok" : "fail"}">${x.ok ? JW.fmt(x.count) : "failed"}</span></li>`).join("");

  // First-run postings are left out of "new", as in status.json.
  const fresh = d.rows.filter(r => !r.first_run && r.first_seen === d.runDate);
  const gone = d.rows.filter(r => r.removed_date === d.runDate);
  $("newh").textContent = `New in the latest run (${JW.fmt(fresh.length)})`;
  $("remh").textContent = `Removed in the latest run (${JW.fmt(gone.length)})`;
  list($("newl"), fresh, "No new postings in the latest run.");
  list($("reml"), gone, "No postings were removed in the latest run.");
}).catch(e => { JW.banner($("banner"), null, e); $("lastrun").textContent = ""; });
