#!/usr/bin/env python3
"""Fetch TLV->Europe flights via SerpApi Google Flights engine.

Usage:
  python3 fetch_serpapi.py test     # 1 query (Italy+Greece, Aug 12->19) to validate
  python3 fetch_serpapi.py run      # full collection (55 date pairs, 5-9 nights)

Key: put your SerpApi key in .serpapi_key (gitignored) or env SERPAPI_KEY.
Budget-aware: prints a running query count.
"""
import sys, os, json, time, ssl, urllib.parse, urllib.request, datetime, collections

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl._create_unverified_context()  # python.org macOS often lacks system CA bundle

PRICE_CAP = 2400          # NIS
ORIGIN = "TLV"
CURRENCY = "ILS"

# Airports per country reachable-ish from TLV (IATA -> (city, country))
AIRPORTS = {
 # Italy
 "FCO":("Rome","Italy"),"MXP":("Milan","Italy"),"BGY":("Milan Bergamo","Italy"),"LIN":("Milan","Italy"),
 "NAP":("Naples","Italy"),"VCE":("Venice","Italy"),"TSF":("Venice Treviso","Italy"),"BLQ":("Bologna","Italy"),
 "BRI":("Bari","Italy"),"CTA":("Catania","Italy"),"PMO":("Palermo","Italy"),"PSA":("Pisa","Italy"),
 "VRN":("Verona","Italy"),"TRN":("Turin","Italy"),"CAG":("Cagliari","Italy"),"BDS":("Brindisi","Italy"),
 # Greece
 "ATH":("Athens","Greece"),"SKG":("Thessaloniki","Greece"),"HER":("Heraklion","Greece"),"RHO":("Rhodes","Greece"),
 "CFU":("Corfu","Greece"),"KGS":("Kos","Greece"),"JMK":("Mykonos","Greece"),"JTR":("Santorini","Greece"),
 "CHQ":("Chania","Greece"),"ZTH":("Zakynthos","Greece"),"JSI":("Skiathos","Greece"),"PVK":("Preveza","Greece"),
 # Spain
 "BCN":("Barcelona","Spain"),"MAD":("Madrid","Spain"),"AGP":("Malaga","Spain"),"VLC":("Valencia","Spain"),
 "PMI":("Palma","Spain"),"ALC":("Alicante","Spain"),"IBZ":("Ibiza","Spain"),"SVQ":("Seville","Spain"),
 # Germany
 "BER":("Berlin","Germany"),"FRA":("Frankfurt","Germany"),"MUC":("Munich","Germany"),"DUS":("Dusseldorf","Germany"),
 "HAM":("Hamburg","Germany"),"CGN":("Cologne","Germany"),"STR":("Stuttgart","Germany"),"NUE":("Nuremberg","Germany"),
 # Austria
 "VIE":("Vienna","Austria"),"SZG":("Salzburg","Austria"),"INN":("Innsbruck","Austria"),"GRZ":("Graz","Austria"),
 # Switzerland
 "ZRH":("Zurich","Switzerland"),"GVA":("Geneva","Switzerland"),"BSL":("Basel","Switzerland"),
 # Croatia
 "ZAG":("Zagreb","Croatia"),"SPU":("Split","Croatia"),"DBV":("Dubrovnik","Croatia"),"ZAD":("Zadar","Croatia"),
 "PUY":("Pula","Croatia"),"RJK":("Rijeka","Croatia"),
 # Denmark
 "CPH":("Copenhagen","Denmark"),"BLL":("Billund","Denmark"),"AAL":("Aalborg","Denmark"),
 # France
 "CDG":("Paris","France"),"ORY":("Paris Orly","France"),"NCE":("Nice","France"),"LYS":("Lyon","France"),
 "MRS":("Marseille","France"),"BOD":("Bordeaux","France"),"TLS":("Toulouse","France"),"NTE":("Nantes","France"),
 # England / UK
 "LHR":("London","England"),"LGW":("London Gatwick","England"),"STN":("London Stansted","England"),
 "LTN":("London Luton","England"),"MAN":("Manchester","England"),"BHX":("Birmingham","England"),
 "EDI":("Edinburgh","England"),"BRS":("Bristol","England"),
 # Belgium
 "BRU":("Brussels","Belgium"),"CRL":("Brussels Charleroi","Belgium"),
 # Netherlands
 "AMS":("Amsterdam","Netherlands"),"EIN":("Eindhoven","Netherlands"),"RTM":("Rotterdam","Netherlands"),
 # Czechia
 "PRG":("Prague","Czechia"),"BRQ":("Brno","Czechia"),
 # Hungary
 "BUD":("Budapest","Hungary"),"DEB":("Debrecen","Hungary"),
 # Portugal
 "LIS":("Lisbon","Portugal"),"OPO":("Porto","Portugal"),"FAO":("Faro","Portugal"),
}

def api_key():
    k = os.environ.get("SERPAPI_KEY")
    if k: return k.strip()
    p = os.path.join(os.path.dirname(__file__), ".serpapi_key")
    if os.path.exists(p):
        return open(p).read().strip()
    sys.exit("No API key. Put it in .serpapi_key or set SERPAPI_KEY.")

KEY = None
QCOUNT = 0

COUNTRY_KGMID = {
    "Italy":"/m/03rjj","Greece":"/m/035qy","Spain":"/m/06mkj","Germany":"/m/0345h","Croatia":"/m/01pj7",
}

def search(arrival_id, dep, ret):
    """One SerpApi google_flights query (arrival_id = airport or country kgmid). Returns (raw, flights)."""
    global QCOUNT
    params = {
        "engine":"google_flights","departure_id":ORIGIN,"arrival_id":arrival_id,
        "outbound_date":dep,"return_date":ret,"currency":CURRENCY,"hl":"en","gl":"il",
        "type":"1","travel_class":"1","stops":"1","deep_search":"true","api_key":KEY,
    }
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    QCOUNT += 1
    with urllib.request.urlopen(url, timeout=90, context=SSL_CTX) as r:
        data = json.loads(r.read().decode())
    if "error" in data:
        return data, []
    out = []
    for bucket in ("best_flights","other_flights"):
        for it in data.get(bucket, []):
            price = it.get("price"); legs = it.get("flights", [])
            if price is None or not legs: continue
            if len(legs) != 1:          # outbound must be a single (nonstop) leg
                continue
            a = legs[0].get("arrival_airport", {})
            out.append({"arr":a.get("id"), "arr_name":a.get("name",""),
                        "price":price, "airline":legs[0].get("airline",""),
                        "dur":it.get("total_duration")})
    return data, out

def clean_city(name, iata):
    n = (name or "").replace(" Airport","").strip()
    return n or iata

def parse_cheapest(flights, country):
    """Cheapest <=cap per arrival airport; label with queried country + API airport name."""
    best = {}
    for f in flights:
        if f["price"] is None or f["price"] > PRICE_CAP: continue
        arr = f["arr"]
        cur = best.get(arr)
        if cur is None or f["price"] < cur["price"]:
            city = AIRPORTS[arr][0] if arr in AIRPORTS else clean_city(f["arr_name"], arr)
            best[arr] = {"airport":arr,"city":city,"country":country,
                         "price":f["price"],"airline":f["airline"],"dur":f["dur"]}
    return best

def date_pairs():
    pairs=[]; start,end=datetime.date(2026,8,9),datetime.date(2026,8,26); d=start
    while d<=end:
        for n in range(5,10):
            r=d+datetime.timedelta(days=n)
            if r<=end: pairs.append((d.isoformat(),r.isoformat(),n))
        d+=datetime.timedelta(days=1)
    return pairs

ALL_AIRPORTS = ",".join(AIRPORTS.keys())

RUN_COUNTRIES = ["Italy","Greece","Spain","Germany","Croatia"]

def selected_pairs():
    """55 pairs minus 7 evenly-spaced -> 48 pairs (fits 48*5=240 queries)."""
    pairs = date_pairs()
    keep = [p for i,p in enumerate(pairs) if i % 8 != 0]   # drop indices 0,8,16,...,48
    dropped = [p for i,p in enumerate(pairs) if i % 8 == 0]
    return keep, dropped

def main():
    global KEY; KEY = api_key()
    mode = sys.argv[1] if len(sys.argv)>1 else "test"
    if mode=="test":
        raw, flights = search(COUNTRY_KGMID["Italy"], "2026-08-12","2026-08-19")
        best = parse_cheapest(flights, "Italy")
        print(f"queries used: {QCOUNT} | Italy cities:")
        for b in sorted(best.values(), key=lambda x:x["price"]):
            print(f"  {b['city']:<16} ₪{b['price']:<5} {b['airline']:<22} {b['dur']}min [{b['airport']}]")
    elif mode=="run":
        keep, dropped = selected_pairs()
        print(f"{len(keep)} date pairs x {len(RUN_COUNTRIES)} countries = {len(keep)*len(RUN_COUNTRIES)} queries")
        print("skipped dates:", [f"{d}->{r}" for d,r,n in dropped])
        results = {}
        for (dep,ret,n) in keep:
            merged = {}
            for c in RUN_COUNTRIES:
                try:
                    _, fl = search(COUNTRY_KGMID[c], dep, ret)
                except Exception as e:
                    print(f"  ! {dep} {c} error: {e}"); continue
                merged.update(parse_cheapest(fl, c))
                time.sleep(0.5)
            results[f"{dep}_{ret}"] = {"dep":dep,"ret":ret,"nights":n,
                                       "flights":sorted(merged.values(), key=lambda x:x["price"])}
            json.dump(results, open("serp_results.json","w"), indent=1)
            print(f"  {dep}->{ret} ({n}n): {len(merged)} dests   [q={QCOUNT}]")
        print(f"\nDONE. total queries this run: {QCOUNT}. results -> serp_results.json")
    else:
        sys.exit("mode must be 'test' or 'run'")

if __name__=="__main__":
    main()
