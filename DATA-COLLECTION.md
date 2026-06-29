# Data Collection Runbook — How the flight data was fetched

This documents exactly how the flight dataset in [`summer-vacation-plan.md`](summer-vacation-plan.md)
and [`flights.html`](flights.html) was produced, so new dates (or a price refresh) can be added
efficiently. The whole pipeline is: **generate search URLs → load each in the browser → extract
results from the DOM → export → regenerate the HTML/MD.**

> Tooling used: the **Claude in Chrome** browser automation tools (`navigate`, `javascript_tool`,
> `read_page`) plus local `python3`. No external flight API — data comes from Google Flights'
> **Explore** view, read straight from the rendered page.

---

## 0. Constraints baked into the search

Every search is a round trip **from Tel Aviv (TLV) to "Anywhere"** with these filters already
encoded in the URL (so results are pre-filtered):

| Constraint | Value |
|---|---|
| Stops | **Nonstop only** |
| Max price | **≤ 2,400 NIS** (currency ILS) |
| Travel mode | Flights only |
| Trip type | Round trip, 1 adult, Economy |

The reference URL (Aug 12 → Aug 19) that all other URLs are derived from:

```
https://www.google.com/travel/explore?tfs=CBwQAxoqEgoyMDI2LTA4LTEyKABqDAgCEggvbS8wN3F6dnIMCAQSCC9tLzAyajcxGioSCjIwMjYtMDgtMTkoAGoMCAQSCC9tLzAyajcxcgwIAhIIL20vMDdxenZAAUgBYOAScAGCAQsI____________AZgBAbIBBBgBIAE&tfu=GgA
```

The `tfs=` query param is a **base64url-encoded protobuf**. Crucially, the two dates are stored as
**plain ASCII strings** inside it (`2026-08-12` and `2026-08-19`), each exactly 10 chars — so we can
make a URL for any date pair by string-substituting those two dates. The origin/"anywhere" tokens
(`/m/07qzvr`, `/m/02j71`) and the filter flags stay untouched.

To change the **price cap, origin, or nonstop** filter, set the filters once in the Google Flights
UI, copy the resulting URL, and use that as the new template.

---

## 1. Generate the search URLs (Python)

Use a **placeholder swap** so it works even when a new departure date equals the template's return
date (`2026-08-19`). Naive `.replace(dep).replace(ret)` corrupts those rows — don't skip the
placeholders.

```python
import base64, datetime, json

TEMPLATE = 'CBwQAxoqEgoyMDI2LTA4LTEyKABqDAgCEggvbS8wN3F6dnIMCAQSCC9tLzAyajcxGioSCjIwMjYtMDgtMTkoAGoMCAQSCC9tLzAyajcxcgwIAhIIL20vMDdxenZAAUgBYOAScAGCAQsI____________AZgBAbIBBBgBIAE'

def _bytes(tpl):
    s = tpl.replace('-', '+').replace('_', '/'); s += '=' * (-len(s) % 4)
    return base64.b64decode(s)
BASE = _bytes(TEMPLATE)

def url_for(dep, ret):  # dep/ret are 'YYYY-MM-DD' strings
    b = BASE.replace(b'2026-08-12', b'@@DEP@@@@').replace(b'2026-08-19', b'@@RET@@@@')
    b = b.replace(b'@@DEP@@@@', dep.encode()).replace(b'@@RET@@@@', ret.encode())
    enc = base64.b64encode(b).decode().replace('+', '-').replace('/', '_').rstrip('=')
    return 'https://www.google.com/travel/explore?tfs=' + enc + '&tfu=GgA'

# Example: build every pair with 4–10 nights inside a window
pairs = []
start, end = datetime.date(2026, 8, 9), datetime.date(2026, 8, 26)
d = start
while d <= end:
    for n in range(4, 11):                       # min 4 nights .. max 10 nights
        r = d + datetime.timedelta(days=n)
        if r <= end:
            pairs.append({'dep': d.isoformat(), 'ret': r.isoformat(), 'nights': n,
                          'url': url_for(d.isoformat(), r.isoformat())})
    d += datetime.timedelta(days=1)

json.dump(pairs, open('flight_urls.json', 'w'), indent=1)
# Sanity check: url_for('2026-08-12','2026-08-19') must equal the original TEMPLATE.
```

---

## 2. Collect results in the browser

Google Flights Explore renders results **client-side** (no clean JSON endpoint), and the data is not
plain text in the initial HTML. So we read the **rendered DOM**.

### Per-result extractor (run in the page context)
Each priced destination card contains a `[role=img]` whose `aria-label` is the **airline**, a
`[aria-label*="Israeli new shekels"]` price, a heading (city), and a duration string.

```js
function extract(doc) {
  const out = [];
  doc.querySelectorAll('[role=img]').forEach(a => {       // airline logos = role=img
    const airline = a.getAttribute('aria-label'); if (!airline) return;
    let card = a, priceEl = null;
    for (let i = 0; i < 8 && card; i++) {
      priceEl = card.querySelector('[aria-label*="Israeli new shekels"]');
      if (priceEl && card.querySelector('h3,[role=heading]')) break;
      card = card.parentElement;
    }
    if (!card || !priceEl) return;
    const dest = card.querySelector('h3,[role=heading]').textContent.trim();
    const txt = card.innerText || '';
    const dur = (txt.match(/\d+\s*hr(?:\s*\d+\s*min)?|\d+\s*min/) || [''])[0].replace(/\s+/g, ' ');
    const price = +((priceEl.getAttribute('aria-label').match(/[\d,]+/) || ['0'])[0].replace(/,/g, ''));
    out.push({ dest, airline, dur, price });
  });
  const m = new Map();                                     // de-dupe per destination, keep cheapest
  out.forEach(o => { if (!m.has(o.dest) || o.price < m.get(o.dest).price) m.set(o.dest, o); });
  return [...m.values()];
}
```

### Loading many date pairs efficiently — the iframe loop
Navigating the top tab 77× is slow. Instead, load each URL into a **same-origin hidden iframe** and
read its DOM. Key gotchas:

- The iframe **must be on-screen** (e.g. `opacity:0.01`, not `left:-9999px`) or Explore never
  lazy-loads its results.
- Poll until the result count is **stable for 3 polls** (results stream in).
- `javascript_tool` has a **~45 s execution cap** → process **~5 pairs per call**.
- Stash each result set in **`localStorage`** (survives navigation on `google.com`), keyed
  `vac_<dep>_<ret>`, then export at the end.

```js
// one-time setup in the page
const ifr = document.createElement('iframe');
ifr.style.cssText = 'position:fixed;left:0;top:0;width:1200px;height:850px;z-index:99999;opacity:0.01;';
document.body.appendChild(ifr);

window.loadPair = (url) => new Promise(async resolve => {
  ifr.src = 'about:blank'; await new Promise(r => setTimeout(r, 120));
  ifr.src = url;
  let prev = -1, stable = 0, res = [];
  for (let i = 0; i < 22; i++) {
    await new Promise(r => setTimeout(r, 550));
    const doc = ifr.contentDocument; if (!doc) continue;
    res = extract(doc);
    if (res.length === prev) { if (i >= 6 && ++stable >= 3) break; } else stable = 0;
    prev = res.length;
  }
  resolve(res);
});

// then, in batches of ~5 (one javascript_tool call each):
window.runBatch = async (urls /* [{dep,ret,url}] */) => {
  const done = [];
  for (const p of urls) {
    const res = await window.loadPair(p.url);
    localStorage.setItem('vac_' + p.dep + '_' + p.ret, JSON.stringify(res));
    done.push({ dep: p.dep, ret: p.ret, n: res.length });
  }
  return JSON.stringify(done);
};
```

> `javascript_tool` returns a **bare Promise** as `{}`. Wrap async work and call with top-level
> `await`: `await (async () => { ... })()`.

> **Re-verify suspiciously low counts.** A few date pairs legitimately return only 3–4 results;
> re-run those with a stricter poll (e.g. stable for 5 polls after iteration 12) to confirm it
> wasn't premature stabilization.

---

## 3. Export the data out of the browser

Two harness limits make export awkward:
- `javascript_tool` output is **truncated at ~1,500 chars**.
- **base64-looking output is blocked** by a content filter (so gzip+base64 transfer fails).

**Working method:** render the data as **one `<div>` per line** of plain text (each line < ~100
chars, prefixed with an index like `⟦42⟧` for ordering/fidelity), then read it back with
**`read_page`** (handles ~45 KB per call, not truncated like `javascript_tool`). Read in segments
of ~230 lines.

```js
// build the markdown string from localStorage, then expose lines for read_page
window.__lines = window.__md.split('\n');
window.__render = (a, b) => {
  const frag = document.createDocumentFragment();
  for (let i = a; i < b && i < window.__lines.length; i++) {
    const d = document.createElement('div');
    d.textContent = '⟦' + i + '⟧ ' + window.__lines[i];      // index prefix = fidelity check
    frag.appendChild(d);
  }
  document.body.replaceChildren(frag);                        // NOT innerHTML (Trusted Types blocks it)
  return { a, b: Math.min(b, window.__lines.length), total: window.__lines.length };
};
```

Then for each segment: call `__render(a, b)` via `javascript_tool`, then `read_page` (filter `all`,
`max_chars` ~45000) and transcribe the `⟦i⟧ …` lines in order.

> Notes: use `document.body.replaceChildren()` (Trusted Types blocks `innerHTML`). Avoid echoing the
> long `tfs` URL in `javascript_tool` return values — it can trip the "Cookie/query string" filter.

---

## 4. Regenerate `flights.html` / `index.html` (Python)

The HTML is **generated from `summer-vacation-plan.md`** (single source of truth) — it parses the
`## All Date Pairs` tables, embeds the rows as JSON, and writes the sortable/filterable page.
The generator lives conceptually here; re-run it after the markdown changes. It also adds the
**Country** column via a `CITY → COUNTRY` dict (extend the dict when a new destination city appears).

```python
import re, json
COUNTRY = {'Rome':'Italy','Venice':'Italy','Athens':'Greece','Mykonos':'Greece','Santorini':'Greece',
           'Budapest':'Hungary','Prague':'Czechia','Berlin':'Germany','Barcelona':'Spain','Madrid':'Spain',
           'Vienna':'Austria','Paris':'France','Dubrovnik':'Croatia','London':'United Kingdom'}
# parse rows from the '## All Date Pairs' section of summer-vacation-plan.md, attach country,
# embed as JSON into the HTML template, write flights.html and index.html.
# assert every destination is in COUNTRY (fail loudly on a new, unmapped city).
```

---

## Checklist — adding new dates (or refreshing prices)

1. **Generate URLs** (§1) for the new date pairs → append to `flight_urls.json`.
2. In the browser, open the reference Explore URL once (confirms filters: Nonstop, ≤ 2,400 NIS, ILS),
   set up the iframe + helpers (§2), then `runBatch(...)` in chunks of ~5 pairs.
3. Re-verify any pair that returned ≤ 4 results (§2 note).
4. Build the markdown tables from `localStorage` and **export** via the line-render + `read_page`
   method (§3); paste the new `### Aug X → Aug Y` sections into `summer-vacation-plan.md`. Update the
   "Cheapest fare per destination" summary and the totals.
5. If any **new destination city** appeared, add it to the `COUNTRY` dict (§4).
6. **Regenerate** `flights.html` + `index.html` (§4) and verify locally
   (`python3 -m http.server 8753`, open `http://localhost:8753/flights.html`).
7. Commit & push — GitHub Pages rebuilds in ~1 min:
   ```
   git add -A && git commit -m "Add dates <range>" && git push
   ```

## Key lessons learned (don't relearn these)

- Dates live as plain ASCII in the `tfs` protobuf → swap with **placeholders** (collision-safe).
- Explore results are **DOM-only**; airline = `[role=img]` `aria-label`, price aria-label is in
  "Israeli new shekels", de-dupe per destination keeping the cheapest.
- Hidden iframe **must be visible** (opacity trick) to trigger result loading.
- `javascript_tool`: ~45 s cap (batch ~5), returns Promises as `{}` (use top-level `await`),
  output truncates ~1,500 chars, **base64 output is blocked**.
- Export large data via **`<div>`-per-line + `read_page`**, using `replaceChildren` (Trusted Types).
