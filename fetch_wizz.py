#!/usr/bin/env python3
"""Convert wizz_raw.json (scraped from wizzair.com fare-finder) to serp_results.json format.

Merges with existing serp_results.json rather than replacing it.
Run: python3 fetch_wizz.py
"""
import json

CITY_IATA = {
    "Rome Fiumicino": "FCO",
    "Naples": "NAP",
    "Milan Malpensa": "MXP",
    "Palermo (Sicily)": "PMO",
    "Sofia": "SOF",
    "Varna (Black Sea)": "VAR",
    "Budapest": "BUD",
    "Athens": "ATH",
    "Bucharest Otopeni": "OTP",
    "Kraków": "KRK",
    "Warsaw Chopin": "WAW",
    "Larnaca": "LCA",
    "Bratislava": "BTS",
    "London Luton": "LTN",
    "Vilnius": "VNO",
}

IATA_COUNTRY = {
    "FCO": "Italy", "NAP": "Italy", "MXP": "Italy", "PMO": "Italy",
    "SOF": "Bulgaria", "VAR": "Bulgaria",
    "BUD": "Hungary",
    "ATH": "Greece",
    "OTP": "Romania",
    "KRK": "Poland", "WAW": "Poland",
    "LCA": "Cyprus",
    "BTS": "Slovakia",
    "LTN": "UK",
    "VNO": "Lithuania",
}

IATA_CITY = {
    "FCO": "Rome", "NAP": "Naples", "MXP": "Milan", "PMO": "Palermo",
    "SOF": "Sofia", "VAR": "Varna",
    "BUD": "Budapest",
    "ATH": "Athens",
    "OTP": "Bucharest",
    "KRK": "Kraków", "WAW": "Warsaw",
    "LCA": "Larnaca",
    "BTS": "Bratislava",
    "LTN": "London",
    "VNO": "Vilnius",
}

def process():
    raw = json.load(open("wizz_raw.json"))

    try:
        existing = json.load(open("serp_results.json"))
    except FileNotFoundError:
        existing = {}

    added = 0
    for key, dp in raw.items():
        wizz_flights = []
        for d in dp["dests"]:
            iata = CITY_IATA.get(d["city"])
            if not iata:
                print(f"  WARNING: no IATA for city '{d['city']}' — skipping")
                continue
            country = IATA_COUNTRY.get(iata, "Unknown")
            city = IATA_CITY.get(iata, d["city"])
            wizz_flights.append({
                "airport": iata,
                "city": city,
                "country": country,
                "price": d["nis"],
                "airline": "Wizz Air",
                "dur": d["dur"],
            })

        if key in existing:
            # Merge: add Wizz Air flights not already present (by airport)
            existing_airports = {f["airport"] for f in existing[key]["flights"]}
            new_wf = [f for f in wizz_flights if f["airport"] not in existing_airports]
            existing[key]["flights"].extend(new_wf)
            existing[key]["flights"].sort(key=lambda x: x["price"])
            added += len(new_wf)
        else:
            existing[key] = {
                "dep": dp["dep"],
                "ret": dp["ret"],
                "nights": dp["nights"],
                "flights": sorted(wizz_flights, key=lambda x: x["price"]),
            }
            added += len(wizz_flights)

    json.dump(existing, open("serp_results.json", "w"), indent=1)
    total = sum(len(v["flights"]) for v in existing.values())
    print(f"Merged wizz_raw.json into serp_results.json")
    print(f"Added {added} Wizz Air flights | Total: {len(existing)} date pairs, {total} flights")

if __name__ == "__main__":
    process()
