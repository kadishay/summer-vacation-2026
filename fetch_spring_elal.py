#!/usr/bin/env python3
"""Merge spring_elal_raw.json (scraped from El Al InspireMe) into spring_results.json.

spring_elal_raw.json format mirrors elal_raw.json:
  {"2027-03-28_2027-04-04": {"dep":"2027-03-28","ret":"2027-04-04","nights":7,
    "dests":[{"dest":"City - IATA","iata":"IATA","usd":N}]}}

Run AFTER fetch_spring.py has written spring_results.json:
  python3 fetch_spring_elal.py

Merges El Al flights into spring_results.json — adds new date pairs and destinations,
keeps the cheaper price when a destination already exists from SerpAPI.
"""
import json, datetime, sys

USD_TO_NIS = 3.0  # 1 USD = 3 NIS per user

IATA_CITY_COUNTRY = {
    # Italy
    "FCO":("Rome","Italy"),"MXP":("Milan","Italy"),"BGY":("Milan Bergamo","Italy"),
    "LIN":("Milan","Italy"),"NAP":("Naples","Italy"),"VCE":("Venice","Italy"),
    "TSF":("Venice Treviso","Italy"),"BLQ":("Bologna","Italy"),"BRI":("Bari","Italy"),
    "CTA":("Catania","Italy"),"PMO":("Palermo","Italy"),"PSA":("Pisa","Italy"),
    "VRN":("Verona","Italy"),"TRN":("Turin","Italy"),"CAG":("Cagliari","Italy"),"BDS":("Brindisi","Italy"),
    # Greece
    "ATH":("Athens","Greece"),"SKG":("Thessaloniki","Greece"),"HER":("Heraklion","Greece"),
    "RHO":("Rhodes","Greece"),"CFU":("Corfu","Greece"),"KGS":("Kos","Greece"),
    "JMK":("Mykonos","Greece"),"JTR":("Santorini","Greece"),"CHQ":("Chania","Greece"),
    "ZTH":("Zakynthos","Greece"),"JSI":("Skiathos","Greece"),"PVK":("Preveza","Greece"),
    # Spain
    "BCN":("Barcelona","Spain"),"MAD":("Madrid","Spain"),"AGP":("Malaga","Spain"),
    "VLC":("Valencia","Spain"),"PMI":("Palma","Spain"),"ALC":("Alicante","Spain"),
    "IBZ":("Ibiza","Spain"),"SVQ":("Seville","Spain"),
    # Germany
    "BER":("Berlin","Germany"),"FRA":("Frankfurt","Germany"),"MUC":("Munich","Germany"),
    "DUS":("Dusseldorf","Germany"),"HAM":("Hamburg","Germany"),"CGN":("Cologne","Germany"),
    "STR":("Stuttgart","Germany"),"NUE":("Nuremberg","Germany"),
    # Austria
    "VIE":("Vienna","Austria"),"SZG":("Salzburg","Austria"),"INN":("Innsbruck","Austria"),"GRZ":("Graz","Austria"),
    # Switzerland
    "ZRH":("Zurich","Switzerland"),"GVA":("Geneva","Switzerland"),"BSL":("Basel","Switzerland"),
    # Croatia
    "ZAG":("Zagreb","Croatia"),"SPU":("Split","Croatia"),"DBV":("Dubrovnik","Croatia"),
    "ZAD":("Zadar","Croatia"),"PUY":("Pula","Croatia"),"RJK":("Rijeka","Croatia"),
    # Slovenia
    "LJU":("Ljubljana","Slovenia"),
    # Denmark
    "CPH":("Copenhagen","Denmark"),"BLL":("Billund","Denmark"),"AAL":("Aalborg","Denmark"),
    # France
    "CDG":("Paris","France"),"ORY":("Paris Orly","France"),"NCE":("Nice","France"),
    "LYS":("Lyon","France"),"MRS":("Marseille","France"),"BOD":("Bordeaux","France"),
    "TLS":("Toulouse","France"),"NTE":("Nantes","France"),
    # UK / England
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
    # Cyprus
    "LCA":("Larnaca","Cyprus"),"PFO":("Paphos","Cyprus"),
    # UAE
    "DXB":("Dubai","UAE"),"AUH":("Abu Dhabi","UAE"),
    # Russia
    "DME":("Moscow","Russia"),"SVO":("Moscow","Russia"),"LED":("St. Petersburg","Russia"),
    # Turkey
    "IST":("Istanbul","Turkey"),"SAW":("Istanbul Sabiha","Turkey"),"AYT":("Antalya","Turkey"),
    # Egypt
    "CAI":("Cairo","Egypt"),"HRG":("Hurghada","Egypt"),"SSH":("Sharm el-Sheikh","Egypt"),
    # Jordan
    "AMM":("Amman","Jordan"),
    # Romania
    "OTP":("Bucharest","Romania"),"CLJ":("Cluj-Napoca","Romania"),"TSR":("Timisoara","Romania"),
    # Bulgaria
    "SOF":("Sofia","Bulgaria"),"VAR":("Varna","Bulgaria"),"BOJ":("Burgas","Bulgaria"),
    # Poland
    "WAW":("Warsaw","Poland"),"KRK":("Kraków","Poland"),"GDN":("Gdańsk","Poland"),"WRO":("Wrocław","Poland"),
    # Serbia
    "BEG":("Belgrade","Serbia"),
    # Montenegro
    "TGD":("Podgorica","Montenegro"),"TIV":("Tivat","Montenegro"),
    # Georgia
    "TBS":("Tbilisi","Georgia"),"BUS":("Batumi","Georgia"),
    # Armenia
    "EVN":("Yerevan","Armenia"),
    # Malta
    "MLA":("Malta","Malta"),
    # Sweden
    "ARN":("Stockholm","Sweden"),"GOT":("Gothenburg","Sweden"),
    # Norway
    "OSL":("Oslo","Norway"),
    # Finland
    "HEL":("Helsinki","Finland"),
    # Ireland
    "DUB":("Dublin","Ireland"),
    # Latvia
    "RIX":("Riga","Latvia"),
    # Lithuania
    "VNO":("Vilnius","Lithuania"),
    # Estonia
    "TLL":("Tallinn","Estonia"),
}

PRICE_CAP = 3000  # 1000 USD × 3 NIS/USD

def city_from_dest(dest_str, iata):
    if iata in IATA_CITY_COUNTRY:
        return IATA_CITY_COUNTRY[iata][0]
    return iata  # fall back to raw IATA code; Hebrew names are intentionally skipped

def merge():
    try:
        raw = json.load(open("spring_elal_raw.json"))
    except FileNotFoundError:
        sys.exit("spring_elal_raw.json not found. Run browser scraping first.")

    try:
        results = json.load(open("spring_results.json"))
    except FileNotFoundError:
        results = {}

    added = updated = skipped = 0
    for key, dp in raw.items():
        dep, ret, nights = dp["dep"], dp["ret"], dp["nights"]

        # Build a dict of current cheapest per airport for this date pair
        existing = {f["airport"]: f for f in results.get(key, {}).get("flights", [])}

        for d in dp.get("dests", []):
            iata = d["iata"]
            usd = d["usd"]
            nis = round(usd * USD_TO_NIS)
            if nis > PRICE_CAP:
                skipped += 1
                continue

            info = IATA_CITY_COUNTRY.get(iata)
            city = city_from_dest(d["dest"], iata)
            country = info[1] if info else "Unknown"

            flight = {"airport": iata, "city": city, "country": country,
                      "price": nis, "airline": "El Al", "dur": None}

            if iata not in existing or nis < existing[iata]["price"]:
                existing[iata] = flight
                if iata not in existing:
                    added += 1
                else:
                    updated += 1

        if existing:
            results[key] = {
                "dep": dep, "ret": ret, "nights": nights,
                "flights": sorted(existing.values(), key=lambda x: x["price"]),
            }

    json.dump(results, open("spring_results.json", "w"), indent=1)
    total = sum(len(v["flights"]) for v in results.values())
    print(f"Merged El Al into spring_results.json")
    print(f"  Date pairs: {len(results)}  |  Total flights: {total}")
    print(f"  El Al: {added} added, {updated} updated cheaper, {skipped} over cap")
    print(f"  USD→NIS rate: {USD_TO_NIS}  (≤{PRICE_CAP} NIS / ~${PRICE_CAP//USD_TO_NIS:.0f})")

if __name__ == "__main__":
    merge()
