#!/usr/bin/env python3
"""Convert elal_raw.json (scraped from inspireme.elal.com) to serp_results.json format.

elal_raw.json format:
  {"2026-08-13_2026-08-20": {"dep":"..","ret":"..","nights":7,"dests":[{"dest":"City - IATA","iata":"IATA","usd":N}]}}

Run: python3 fetch_elal.py
"""
import json, datetime

USD_TO_NIS = 3.65  # approximate rate Jul 2026

IATA_COUNTRY = {
    # Italy
    "FCO":"Italy","MXP":"Italy","BGY":"Italy","LIN":"Italy","NAP":"Italy","VCE":"Italy",
    "TSF":"Italy","BLQ":"Italy","BRI":"Italy","CTA":"Italy","PMO":"Italy","PSA":"Italy",
    "VRN":"Italy","TRN":"Italy","CAG":"Italy","BDS":"Italy",
    # Greece
    "ATH":"Greece","SKG":"Greece","HER":"Greece","RHO":"Greece","CFU":"Greece","KGS":"Greece",
    "JMK":"Greece","JTR":"Greece","CHQ":"Greece","ZTH":"Greece","JSI":"Greece","PVK":"Greece",
    # Spain
    "BCN":"Spain","MAD":"Spain","AGP":"Spain","VLC":"Spain","PMI":"Spain","ALC":"Spain",
    "IBZ":"Spain","SVQ":"Spain",
    # Germany
    "BER":"Germany","FRA":"Germany","MUC":"Germany","DUS":"Germany","HAM":"Germany",
    "CGN":"Germany","STR":"Germany","NUE":"Germany",
    # Austria
    "VIE":"Austria","SZG":"Austria","INN":"Austria","GRZ":"Austria",
    # Switzerland
    "ZRH":"Switzerland","GVA":"Switzerland","BSL":"Switzerland",
    # Croatia
    "ZAG":"Croatia","SPU":"Croatia","DBV":"Croatia","ZAD":"Croatia","PUY":"Croatia","RJK":"Croatia",
    # Slovenia
    "LJU":"Slovenia",
    # France
    "CDG":"France","ORY":"France","NCE":"France","LYS":"France","MRS":"France",
    "BOD":"France","TLS":"France","NTE":"France",
    # UK
    "LHR":"UK","LGW":"UK","STN":"UK","LTN":"UK","MAN":"UK","BHX":"UK","EDI":"UK","BRS":"UK",
    # Belgium
    "BRU":"Belgium","CRL":"Belgium",
    # Netherlands
    "AMS":"Netherlands","EIN":"Netherlands","RTM":"Netherlands",
    # Czechia
    "PRG":"Czechia","BRQ":"Czechia",
    # Hungary
    "BUD":"Hungary","DEB":"Hungary",
    # Portugal
    "LIS":"Portugal","OPO":"Portugal","FAO":"Portugal",
    # Denmark
    "CPH":"Denmark","BLL":"Denmark","AAL":"Denmark",
    # Cyprus
    "LCA":"Cyprus","PFO":"Cyprus",
    # Romania
    "OTP":"Romania","CLJ":"Romania","TSR":"Romania",
    # Bulgaria
    "SOF":"Bulgaria","VAR":"Bulgaria","BOJ":"Bulgaria",
    # Poland
    "WAW":"Poland","KRK":"Poland","GDN":"Poland","WRO":"Poland",
    # Serbia
    "BEG":"Serbia",
    # Montenegro
    "TGD":"Montenegro","TIV":"Montenegro",
    # North Macedonia
    "SKP":"North Macedonia",
    # Albania
    "TIA":"Albania",
    # Georgia
    "TBS":"Georgia","BUS":"Georgia",
    # Armenia
    "EVN":"Armenia",
    # Malta
    "MLA":"Malta",
    # Turkey
    "IST":"Turkey","SAW":"Turkey","AYT":"Turkey","ADB":"Turkey","ESB":"Turkey","BJV":"Turkey",
    # Morocco
    "CMN":"Morocco","RAK":"Morocco","TNG":"Morocco",
    # Jordan
    "AMM":"Jordan","AQJ":"Jordan",
    # Egypt
    "CAI":"Egypt","HRG":"Egypt","SSH":"Egypt",
    # UAE
    "DXB":"UAE","AUH":"UAE",
    # Sweden
    "ARN":"Sweden","GOT":"Sweden",
    # Norway
    "OSL":"Norway","BGO":"Norway",
    # Finland
    "HEL":"Finland",
    # Ireland
    "DUB":"Ireland",
    # Luxembourg
    "LUX":"Luxembourg",
    # Iceland
    "KEF":"Iceland",
    # Latvia
    "RIX":"Latvia",
    # Lithuania
    "VNO":"Lithuania",
    # Estonia
    "TLL":"Estonia",
}

def city_from_dest(dest, iata):
    """Extract English city name from 'City Name - IATA' string."""
    if " - " in dest:
        return dest.rsplit(" - ", 1)[0].strip()
    return iata

def process():
    try:
        raw = json.load(open("elal_raw.json"))
    except FileNotFoundError:
        print("elal_raw.json not found. Run browser scraping first.")
        return

    results = {}
    for key, dp in raw.items():
        flights = []
        for d in dp.get("dests", []):
            iata = d["iata"]
            usd = d["usd"]
            nis = round(usd * USD_TO_NIS)
            city = city_from_dest(d["dest"], iata)
            country = IATA_COUNTRY.get(iata, "Unknown")
            flights.append({
                "airport": iata,
                "city": city,
                "country": country,
                "price": nis,
                "price_usd": usd,
                "airline": "El Al",
                "dur": None,
            })
        flights.sort(key=lambda x: x["price"])
        results[key] = {
            "dep": dp["dep"],
            "ret": dp["ret"],
            "nights": dp["nights"],
            "flights": flights,
        }

    json.dump(results, open("serp_results.json", "w"), indent=1)
    total = sum(len(v["flights"]) for v in results.values())
    print(f"Wrote serp_results.json: {len(results)} date pairs, {total} total flights")
    print(f"USD→NIS rate: {USD_TO_NIS}  (prices approximate)")

if __name__ == "__main__":
    process()
