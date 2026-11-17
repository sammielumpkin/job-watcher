/* Shared by all pages: navigation, data loading, helpers, charts, service worker. */
(function () {
  const PAGES = [["index.html", "Today"], ["browse.html", "Browse"], ["market.html", "Market"]];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function nav(page) {
    const el = document.createElement("nav");
    el.className = "nav";
    el.setAttribute("aria-label", "Main");
    el.innerHTML = '<span class="brand">Job Watcher</span>' + PAGES.map(([h, n]) =>
      `<a href="${h}"${h === page ? ' aria-current="page"' : ""}>${n}</a>`).join("");
    document.body.prepend(el);
    const tip = document.createElement("div");
    tip.id = "tip";
    document.body.append(tip);
    const show = e => {
      const t = e.target.closest && e.target.closest("[data-tip]");
      if (!t) { tip.style.display = "none"; return; }
      tip.textContent = t.dataset.tip;
      tip.style.display = "block";
      tip.style.left = Math.min(e.clientX + 12, innerWidth - 250) + "px";
      tip.style.top = (e.clientY + 14) + "px";
    };
    document.addEventListener("mousemove", show);
    document.addEventListener("click", show);
  }

  // Quoted-field CSV parser (handles commas, quotes and newlines inside fields).
  function parseCSV(text) {
    const out = []; let row = [], f = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; }
        else f += c;
      } else if (c === '"') q = true;
      else if (c === ",") { row.push(f); f = ""; }
      else if (c === "\n") { row.push(f); out.push(row); row = []; f = ""; }
      else if (c !== "\r") f += c;
    }
    if (f !== "" || row.length) { row.push(f); out.push(row); }
    const head = out.shift() || [];
    return out.filter(r => r.length > 1).map(r => {
      const o = {}; head.forEach((h, i) => o[h] = r[i] === undefined ? "" : r[i]); return o;
    });
  }

  // Online: the data comes from the network. Offline: the service worker answers from its
  // cache and marks the response with x-jw-offline so the page can say so.
  async function loadData() {
    const get = u => fetch(u, { cache: "no-cache" });
    const [h, s] = await Promise.all([get("data/history.csv"), get("data/status.json")]);
    if (!h.ok || !s.ok) throw new Error("Data files not available (" + h.status + "/" + s.status + ")");
    const offline = h.headers.get("x-jw-offline") === "1" || s.headers.get("x-jw-offline") === "1";
    const rows = parseCSV(await h.text()).map(r => {
      r.in_role = r.in_role === "true"; r.first_run = r.first_run === "true"; return r;
    });
    const status = await s.json();
    return { rows, status, offline, runDate: String(status.run_time).slice(0, 10) };
  }

  function days(a, b) { return Math.round((Date.parse(b) - Date.parse(a)) / 864e5); }
  function median(a) {
    if (!a.length) return null;
    const s = [...a].sort((x, y) => x - y), m = s.length >> 1;
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }
  const fmt = n => Number(n).toLocaleString("en-US");

  function banner(el, data, err) {
    if (err) { el.innerHTML = `<div class="banner err">Could not load data: ${esc(err.message)}</div>`; return; }
    el.innerHTML = data.offline
      ? '<div class="banner">You are offline. Showing the last data this device loaded.</div>' : "";
  }

  /* ---------- charts (plain SVG/HTML, no libraries, so they work offline) ---------- */
  function niceMax(v) {
    if (v <= 4) return 4;
    const p = Math.pow(10, Math.floor(Math.log10(v))), n = v / p;
    return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p;
  }

  // Vertical bars: items [{label, value, tip?}]
  function columns(el, items, label) {
    const draw = () => {
      const W = Math.max(260, el.clientWidth || 600), H = 220, L = 38, B = 26, T = 8, R = 6;
      const max = niceMax(Math.max(1, ...items.map(i => i.value)));
      const iw = (W - L - R) / items.length, bw = Math.max(2, Math.min(36, iw * 0.72));
      const y = v => T + (H - T - B) * (1 - v / max);
      let s = `<svg width="${W}" height="${H}" role="img" aria-label="${esc(label)}">`;
      for (let k = 0; k <= 4; k++) {
        const v = max * k / 4;
        s += `<line class="grid" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>` +
             `<text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${fmt(Math.round(v))}</text>`;
      }
      const every = Math.ceil(items.length / Math.max(1, Math.floor((W - L) / 56)));
      items.forEach((it, i) => {
        const x = L + iw * i + (iw - bw) / 2, h = (H - T - B) * it.value / max;
        const r = Math.min(4, bw / 2, h);
        if (it.value > 0)
          s += `<path class="bar" d="M${x},${y(0)}v${-(h - r)}a${r},${r} 0 0 1 ${r},${-r}h${bw - 2 * r}a${r},${r} 0 0 1 ${r},${r}v${h - r}z"/>`;
        s += `<rect x="${L + iw * i}" y="${T}" width="${iw}" height="${H - T - B}" fill="transparent" data-tip="${esc(it.tip || it.label + ": " + fmt(it.value))}"/>`;
        if (i % every === 0)
          s += `<text x="${L + iw * i + iw / 2}" y="${H - 8}" text-anchor="middle">${esc(it.label)}</text>`;
      });
      el.innerHTML = s + "</svg>";
    };
    draw();
    if (!el._ro) {
      el._ro = new ResizeObserver(() => { if (el._w !== el.clientWidth) { el._w = el.clientWidth; draw(); } });
      el._ro.observe(el);
    }
  }

  // Horizontal bars as HTML rows.
  function hbars(el, items) {
    const max = Math.max(1, ...items.map(i => i.value));
    el.innerHTML = items.map(i =>
      `<div class="hrow" data-tip="${esc(i.label)}: ${fmt(i.value)}"><span class="lab">${esc(i.label)}</span>` +
      `<span class="track"><div class="fill" style="width:${100 * i.value / max}%"></div></span>` +
      `<span class="val">${fmt(i.value)}</span></div>`).join("");
  }

  function table(headers, data) {
    return "<details><summary>Show as table</summary><table><tr>" + headers.map(h => `<th>${esc(h)}</th>`).join("") +
      "</tr>" + data.map(r => "<tr>" + r.map(c => `<td>${esc(c)}</td>`).join("") + "</tr>").join("") + "</table></details>";
  }

  if ("serviceWorker" in navigator)
    addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));

  window.JW = { esc, nav, parseCSV, loadData, days, median, fmt, banner, columns, hbars, table };
})();
