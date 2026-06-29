# Data Collection Runbook — How the flight data was fetched

Flight data in [`flights.html`](flights.html) / [`index.html`](index.html) comes from **SerpApi's
Google Flights engine** (primary method, used for all data as of 2026-06-29). The old Google Flights
Explore browser-scraping method is documented at the bottom as a legacy fallback.

Scripts:
- **`fetch_serpapi.py`** — queries SerpApi and writes `serp_results.json`
- **`build_from_serp.py`** — reads `serp_results.json`, writes `flights.html` / `index.html` / `flight_tables_serp.md`

---

## Method A — SerpApi (current, preferred)

### Why SerpApi over browser scraping

| Problem with browser scraping | SerpApi solution |
|---|---|
| Google Explore shows only ~1 curated city per country | Country kgmid returns **all airports** in country |
| Throttled after ~6 rapid queries (renderer freezes for hours) | No throttling — 250 free queries/month |
| ~45 s per URL, iframe/renderer instability | ~1–2 s per query via HTTP |
| DOM extraction is fragile | Structured JSON response |

### Search constraints

| Constraint | Value |
|---|---|
| Origin | TLV (Tel Aviv) |
| Stops | `stops=1` = **nonstop only** |
| Max price | **≤ 2,400 NIS** (`currency=ILS`) |
| Trip type | Round trip, 1 adult, Economy (`type=1`, `travel_class=1`) |
| Scope | Italy, Greece, Spain, Germany, Croatia × 48 date pairs (Aug 9–26, 5–9 nights) |

### Key insight: country kgmid as `arrival_id`

Passing a **country kgmid** (e.g. `/m/03rjj` for Italy) as `arrival_id` returns all airports in
that country in a single query — replacing what would otherwise be dozens of per-airport queries.

```python
COUNTRY_KGMID = {
    "Italy":   "/m/03rjj",
    "Greece":  "/m/035qy",
    "Spain":   "/m/06mkj",
    "Germany": "/m/0345h",
    "Croatia": "/m/01pj7",
}
```

> **Do not** pass a comma-separated list of airport IATA codes as `arrival_id` — SerpApi returns
> no results for multi-airport CSV. Use airport IATA codes one at a time, or a country kgmid.

### Running a collection

**Prerequisites:** put your SerpApi key in `.serpapi_key` (gitignored) or `$SERPAPI_KEY`.

```bash
# Validate: 1 query (Italy, Aug 12→19), prints cities + prices
python3 fetch_serpapi.py test

# Full collection: 48 date pairs × 5 countries = 240 queries
python3 fetch_serpapi.py run          # writes serp_results.json incrementally

# Rebuild HTML (reads serp_results.json)
python3 build_from_serp.py           # writes flights.html, index.html, flight_tables_serp.md
```

### Budget-aware date pair selection

We have 250 free SerpApi queries/month. With 5 countries, that allows 50 date pairs (250/5).
The full date window (Aug 9–26, 5–9 nights) produces 55 pairs, so we drop 7 (every 8th index):

```python
def selected_pairs():
    pairs = date_pairs()  # all 55 pairs
    return [p for i, p in enumerate(pairs) if i % 8 != 0]  # 48 pairs → 240 queries
```

To add more countries, drop more date pairs to stay within budget, or upgrade the SerpApi plan.

### Adding new date ranges or countries

1. If extending the date window, update `date_pairs()` in `fetch_serpapi.py` (change `start`/`end`).
2. If adding a country, find its kgmid via Google Knowledge Graph, add to `COUNTRY_KGMID`.
   Also add its airports to `AIRPORTS` dict for clean city-name lookup.
3. Re-run `selected_pairs()` logic to ensure total queries ≤ budget.
4. Run `python3 fetch_serpapi.py run` (existing pairs in `serp_results.json` are overwritten).
5. Run `python3 build_from_serp.py` to regenerate HTML.
6. Commit & push → GitHub Pages updates in ~1 min.

### How SerpApi response is parsed

```python
def search(arrival_id, dep, ret):
    """One SerpApi query → list of nonstop flights."""
    params = {
        "engine": "google_flights", "departure_id": "TLV", "arrival_id": arrival_id,
        "outbound_date": dep, "return_date": ret, "currency": "ILS", "hl": "en", "gl": "il",
        "type": "1", "travel_class": "1", "stops": "1", "deep_search": "true", "api_key": KEY,
    }
    # Response buckets: best_flights, other_flights
    # Each item has: price, flights[] (legs), total_duration
    # Filter: len(flights) == 1 → true nonstop outbound leg
```

Cheapest fare per arrival airport is kept; city name comes from the `AIRPORTS` lookup dict (or the
API's `arrival_airport.name` field if not in the dict).

### SSL fix on macOS (python.org install)

Python.org macOS builds often lack the system CA bundle. The script auto-handles this:

```python
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl._create_unverified_context()
```

Run `pip3 install certifi` once to get the clean fix.

---

## Checklist — refreshing data or adding scope

1. **Edit `fetch_serpapi.py`** — update date window, country list, or budget allocation.
2. **Test**: `python3 fetch_serpapi.py test` (1 query) → verify cities + prices look right.
3. **Full run**: `python3 fetch_serpapi.py run` → `serp_results.json` written incrementally.
   - Run is safe to restart: it overwrites `serp_results.json` each pair.
   - Watch the printed query count to stay within budget.
4. **Rebuild HTML**: `python3 build_from_serp.py` → `flights.html`, `index.html`, `flight_tables_serp.md`.
5. **Verify locally**: `python3 -m http.server 8753` → open `http://localhost:8753/`.
6. **Commit & push**:
   ```bash
   git add flights.html index.html flight_tables_serp.md serp_results.json
   git commit -m "Refresh flight data: <date range / countries>"
   git push
   ```
   GitHub Pages live at: `https://kadishay.github.io/summer-vacation-2026/`

---

## Method B — Google Flights Explore (legacy, browser-based)

This method was used for the initial dataset but abandoned due to:
- Google Explore returning only ~1 curated city per country (missed most airports)
- Throttling after ~6 rapid queries (renderer freezes for hours)
- ~45 s per URL + iframe instability

Kept here for reference in case SerpApi quota runs out.

### URL generation (Python)

The `tfs=` param in Explore URLs is a base64url-encoded protobuf where dates are stored as **plain
ASCII** — so any date pair can be produced by string-substituting the template dates. Use a
**placeholder swap** to avoid corruption when new departure date = template return date (`2026-08-19`).

```python
import base64, datetime, json

TEMPLATE = 'CBwQAxoqEgoyMDI2LTA4LTEyKABqDAgCEggvbS8wN3F6dnIMCAQSCC9tLzAyajcxGioSCjIwMjYtMDgtMTkoAGoMCAQSCC9tLzAyajcxcgwIAhIIL20vMDdxenZAAUgBYOAScAGCAQsI____________AZgBAbIBBBgBIAE'

def _bytes(tpl):
    s = tpl.replace('-', '+').replace('_', '/'); s += '=' * (-len(s) % 4)
    return base64.b64decode(s)
BASE = _bytes(TEMPLATE)

def url_for(dep, ret):
    b = BASE.replace(b'2026-08-12', b'@@DEP@@@@').replace(b'2026-08-19', b'@@RET@@@@')
    b = b.replace(b'@@DEP@@@@', dep.encode()).replace(b'@@RET@@@@', ret.encode())
    enc = base64.b64encode(b).decode().replace('+', '-').replace('/', '_').rstrip('=')
    return 'https://www.google.com/travel/explore?tfs=' + enc + '&tfu=GgA'
```

### Browser DOM extraction

Explore renders client-side only. Airline = `[role=img]` `aria-label`. Price = element with
`aria-label` containing "Israeli new shekels". De-dupe per destination, keep cheapest.

Hidden iframe **must be visible** (`opacity:0.01`, not `left:-9999px`) or lazy-loading never fires.

### Export from browser

`javascript_tool` output truncates at ~1,500 chars and base64 output is blocked by content filter.
Working method: render data as **one `<div>` per line** then read via **`read_page`** (~45 KB/call).
Use `document.body.replaceChildren()` — not `innerHTML` (blocked by Trusted Types).

### Async in `javascript_tool`

Bare async IIFE returns `{}`. Always use:
```js
await (async () => { /* your async code */ })()
```
