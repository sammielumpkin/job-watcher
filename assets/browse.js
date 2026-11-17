JW.nav("browse.html");
const $ = id => document.getElementById(id);
const KEY = "jw-shortlist";
const PAGE = 100;

// Shortlist lives in localStorage so it survives a reload (wrapped: storage can be blocked).
function loadStars() {
  try { return new Set(JSON.parse(localStorage.getItem(KEY) || "[]")); } catch (e) { return new Set(); }
}
function saveStars() {
  try { localStorage.setItem(KEY, JSON.stringify([...stars])); } catch (e) {}
}
const stars = loadStars();

let open = [], runDate = "", mode = "role", shown = PAGE;

function fill(sel, values) {
  sel.insertAdjacentHTML("beforeend", values.map(v => `<option>${JW.esc(v)}</option>`).join(""));
}

function filtered() {
  const emp = $("f-emp").value, loc = $("f-loc").value, dr = $("f-days").value;
  const q = $("f-q").value.trim().toLowerCase(), onlyStar = $("f-star").checked;
  const [lo, hi] = dr ? dr.split("-").map(x => x === "" ? Infinity : Number(x)) : [0, Infinity];
  const out = open.filter(r =>
    (mode === "all" || r.in_role) && (!emp || r.employer === emp) && (!loc || r.location === loc) &&
    (!q || r.title.toLowerCase().includes(q)) && (!onlyStar || stars.has(r.posting_id)) &&
    r.daysOpen >= lo && r.daysOpen <= hi);
  const dir = $("f-sort").value === "asc" ? 1 : -1;
  out.sort((a, b) => dir * a.first_seen.localeCompare(b.first_seen) || a.posting_id.localeCompare(b.posting_id));
  return out;
}

function render() {
  const rows = filtered();
  $("count").textContent = `${JW.fmt(rows.length)} posting${rows.length === 1 ? "" : "s"}` +
    ` (${JW.fmt(stars.size)} on shortlist)`;
  $("list").innerHTML = rows.slice(0, shown).map(r => {
    const on = stars.has(r.posting_id);
    return `<div class="post"><button class="star" data-id="${JW.esc(r.posting_id)}" aria-pressed="${on}" ` +
      `aria-label="${on ? "Remove from" : "Add to"} shortlist: ${JW.esc(r.title)}">${on ? "&#9733;" : "&#9734;"}</button>` +
      `<div class="av" aria-hidden="true">${JW.esc(r.employer.charAt(0).toUpperCase())}</div>` +
      `<div><div class="t">${JW.esc(r.title)}</div><div class="meta"><span>${JW.esc(r.employer)}</span>` +
      `${r.location ? "<span>" + JW.esc(r.location) + "</span>" : ""}${r.department ? "<span>" + JW.esc(r.department) + "</span>" : ""}` +
      `<span>First seen ${r.first_seen} (${r.daysOpen} d)</span>${r.posted_date ? "<span>Posted " + r.posted_date + "</span>" : ""}</div></div>` +
      `<a class="apply" href="${JW.esc(r.url)}" target="_blank" rel="noopener">Apply</a></div>`;
  }).join("") || '<p class="muted">No postings match.</p>';
  $("more").hidden = rows.length <= shown;
}

function reset() { shown = PAGE; render(); }

function setMode(m) {
  mode = m;
  for (const [id, k] of [["m-role", "role"], ["m-all", "all"]]) {
    $(id).classList.toggle("on", k === m); $(id).setAttribute("aria-pressed", k === m);
  }
  reset();
}

JW.loadData().then(d => {
  JW.banner($("banner"), d);
  runDate = d.runDate;
  open = d.rows.filter(r => r.status === "open");
  open.forEach(r => r.daysOpen = JW.days(r.first_seen, runDate));
  fill($("f-emp"), [...new Set(open.map(r => r.employer))].sort());
  fill($("f-loc"), [...new Set(open.map(r => r.location).filter(Boolean))].sort());
  render();
}).catch(e => JW.banner($("banner"), null, e));

$("m-role").onclick = () => setMode("role");
$("m-all").onclick = () => setMode("all");
for (const id of ["f-emp", "f-loc", "f-days", "f-sort", "f-star"]) $(id).onchange = reset;
$("f-q").oninput = reset;
$("more").onclick = () => { shown += PAGE; render(); };
$("list").onclick = e => {
  const b = e.target.closest(".star");
  if (!b) return;
  const id = b.dataset.id;
  stars.has(id) ? stars.delete(id) : stars.add(id);
  saveStars();
  render();
};
