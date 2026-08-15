#!/usr/bin/env python3
"""Build spring.html / spring_index.html from spring_results.json.

Adds two columns vs. the summer page: Apr High/Low temp and Apr rain days.
Map dot color reflects weather quality (warm+dry = orange, cool+wet = blue).
"""
import json, datetime

DATA = json.load(open("spring_results.json"))
CAPTURE = datetime.date.today().isoformat()

# April climate averages per city: {high°C, low°C, rain days/month}
CLIMATE = {
    "Rome":         {"high": 18, "low":  9, "rain":  8},
    "Milan":        {"high": 18, "low":  8, "rain": 10},
    "Naples":       {"high": 18, "low": 11, "rain":  9},
    "Venice":       {"high": 16, "low":  8, "rain":  9},
    "Bologna":      {"high": 17, "low":  8, "rain": 10},
    "Bari":         {"high": 19, "low": 11, "rain":  8},
    "Catania":      {"high": 20, "low": 12, "rain":  7},
    "Palermo":      {"high": 20, "low": 13, "rain":  7},
    "Pisa":         {"high": 17, "low":  9, "rain":  9},
    "Verona":       {"high": 17, "low":  7, "rain": 10},
    "Turin":        {"high": 17, "low":  7, "rain": 12},
    "Cagliari":     {"high": 19, "low": 12, "rain":  7},
    "Brindisi":     {"high": 19, "low": 11, "rain":  7},
    "Athens":       {"high": 20, "low": 12, "rain":  7},
    "Thessaloniki": {"high": 19, "low": 10, "rain":  8},
    "Heraklion":    {"high": 21, "low": 14, "rain":  7},
    "Rhodes":       {"high": 21, "low": 14, "rain":  5},
    "Corfu":        {"high": 20, "low": 13, "rain":  9},
    "Kos":          {"high": 21, "low": 14, "rain":  5},
    "Mykonos":      {"high": 18, "low": 13, "rain":  6},
    "Santorini":    {"high": 18, "low": 13, "rain":  6},
    "Chania":       {"high": 21, "low": 14, "rain":  7},
    "Zakynthos":    {"high": 21, "low": 13, "rain":  8},
    "Skiathos":     {"high": 18, "low": 12, "rain":  9},
    "Preveza":      {"high": 20, "low": 12, "rain":  8},
    "Barcelona":    {"high": 18, "low": 10, "rain":  8},
    "Madrid":       {"high": 17, "low":  7, "rain":  9},
    "Malaga":       {"high": 22, "low": 13, "rain":  7},
    "Valencia":     {"high": 21, "low": 12, "rain":  7},
    "Palma":        {"high": 19, "low": 11, "rain":  7},
    "Alicante":     {"high": 22, "low": 12, "rain":  5},
    "Ibiza":        {"high": 20, "low": 12, "rain":  6},
    "Seville":      {"high": 23, "low": 13, "rain":  8},
    "Berlin":       {"high": 13, "low":  5, "rain": 10},
    "Frankfurt":    {"high": 15, "low":  5, "rain": 12},
    "Munich":       {"high": 14, "low":  4, "rain": 12},
    "Dusseldorf":   {"high": 14, "low":  5, "rain": 13},
    "Hamburg":      {"high": 13, "low":  5, "rain": 12},
    "Cologne":      {"high": 14, "low":  5, "rain": 13},
    "Stuttgart":    {"high": 14, "low":  4, "rain": 12},
    "Nuremberg":    {"high": 14, "low":  4, "rain": 11},
    "Vienna":       {"high": 15, "low":  6, "rain": 11},
    "Salzburg":     {"high": 14, "low":  4, "rain": 13},
    "Innsbruck":    {"high": 15, "low":  4, "rain": 11},
    "Graz":         {"high": 15, "low":  5, "rain": 11},
    "Zurich":       {"high": 14, "low":  4, "rain": 13},
    "Geneva":       {"high": 15, "low":  5, "rain": 12},
    "Basel":        {"high": 15, "low":  5, "rain": 12},
    "Zagreb":       {"high": 16, "low":  7, "rain": 11},
    "Split":        {"high": 18, "low": 11, "rain":  9},
    "Dubrovnik":    {"high": 18, "low": 12, "rain": 10},
    "Zadar":        {"high": 17, "low": 10, "rain": 10},
    "Pula":         {"high": 17, "low": 10, "rain": 10},
    "Rijeka":       {"high": 15, "low":  9, "rain": 12},
    "Ljubljana":    {"high": 15, "low":  5, "rain": 12},
    "Copenhagen":   {"high": 12, "low":  5, "rain": 10},
    "Billund":      {"high": 11, "low":  3, "rain": 11},
    "Aalborg":      {"high": 11, "low":  3, "rain": 10},
    "Paris":        {"high": 16, "low":  7, "rain": 11},
    "Nice":         {"high": 17, "low":  9, "rain":  9},
    "Lyon":         {"high": 16, "low":  7, "rain": 12},
    "Marseille":    {"high": 18, "low":  9, "rain":  9},
    "Bordeaux":     {"high": 17, "low":  8, "rain": 12},
    "Toulouse":     {"high": 18, "low":  8, "rain": 11},
    "Nantes":       {"high": 15, "low":  7, "rain": 13},
    "London":       {"high": 13, "low":  6, "rain": 12},
    "Manchester":   {"high": 12, "low":  5, "rain": 14},
    "Birmingham":   {"high": 13, "low":  4, "rain": 12},
    "Edinburgh":    {"high": 11, "low":  4, "rain": 13},
    "Bristol":      {"high": 13, "low":  5, "rain": 13},
    "Brussels":     {"high": 14, "low":  5, "rain": 13},
    "Amsterdam":    {"high": 13, "low":  5, "rain": 12},
    "Eindhoven":    {"high": 13, "low":  5, "rain": 12},
    "Rotterdam":    {"high": 13, "low":  5, "rain": 12},
    "Prague":       {"high": 14, "low":  5, "rain": 10},
    "Brno":         {"high": 15, "low":  5, "rain": 10},
    "Budapest":     {"high": 17, "low":  7, "rain": 10},
    "Debrecen":     {"high": 18, "low":  7, "rain": 10},
    "Lisbon":       {"high": 20, "low": 12, "rain":  9},
    "Porto":        {"high": 19, "low": 10, "rain": 13},
    "Faro":         {"high": 22, "low": 13, "rain":  6},
}

def get_climate(city):
    """Look up climate, handling variants like 'Milan Bergamo', 'Paris Orly', 'London Gatwick'."""
    if city in CLIMATE:
        return CLIMATE[city]
    for base in CLIMATE:
        if city.startswith(base):
            return CLIMATE[base]
    return None

def fmt_dur(mins):
    if not mins: return ""
    h, m = divmod(int(mins), 60)
    return (f"{h} hr" + (f" {m} min" if m else "")) if h else f"{m} min"

def fmt_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%b ") + str(d.day)

rows = []
for key, dp in DATA.items():
    for f in dp["flights"]:
        cl = get_climate(f["city"])
        rows.append({
            "dest": f["city"], "country": f["country"], "airport": f["airport"],
            "price": f["price"], "airline": f["airline"],
            "from": fmt_date(dp["dep"]), "to": fmt_date(dp["ret"]),
            "fromISO": dp["dep"], "toISO": dp["ret"],
            "fromDay": datetime.date.fromisoformat(dp["dep"]).day,
            "toDay": datetime.date.fromisoformat(dp["ret"]).day,
            "nights": dp["nights"], "length": fmt_dur(f["dur"]), "durMin": f["dur"] or 0,
            "tempHigh": cl["high"] if cl else None,
            "tempLow":  cl["low"]  if cl else None,
            "rainDays": cl["rain"] if cl else None,
        })

ndates = len(DATA); nrows = len(rows)
countries = sorted(set(r["country"] for r in rows))

data_json = json.dumps(rows, ensure_ascii=False)
HTML = r'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Spring Break 2027 Flights — TLV → Europe</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
 :root{--bg:#0f1419;--panel:#1a2029;--line:#2b3340;--text:#e6edf3;--muted:#8b98a8;--accent:#4ea1ff;}
 *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
 header{padding:18px 22px 10px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:30}
 h1{margin:0 0 2px;font-size:18px}.sub{color:var(--muted);font-size:13px}
 .controls{display:flex;flex-wrap:wrap;gap:14px;padding:12px 22px;border-bottom:1px solid var(--line);align-items:flex-end;background:var(--panel);position:sticky;top:61px;z-index:20}
 .ctrl{display:flex;flex-direction:column;gap:4px}.ctrl label{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
 select,input{background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:6px 8px;font-size:13px;outline:none}
 input:focus,select:focus{border-color:var(--accent)}input[type=number]{width:90px}.range{display:flex;gap:6px;align-items:center}#search{width:200px}
 button{background:var(--accent);color:#06121f;border:none;border-radius:7px;padding:7px 12px;font-weight:600;cursor:pointer;font-size:13px}button.secondary{background:var(--line);color:var(--text)}
 #map{height:360px;border-bottom:1px solid var(--line);position:relative}
 .count{color:var(--muted);font-size:13px;padding:8px 22px 0}.wrap{padding:6px 22px 60px}
 table{border-collapse:collapse;width:100%}th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
 th{position:sticky;top:118px;background:#10161e;cursor:pointer;user-select:none;font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);z-index:10}
 th:hover{color:var(--text)}th .arrow{color:var(--accent);font-size:11px}tbody tr:hover{background:#161d27}
 td.num{text-align:right;font-variant-numeric:tabular-nums}.price{font-weight:700;color:#7ee2a8}.pill{background:var(--line);border-radius:20px;padding:2px 9px;font-size:12px}.country{color:var(--muted)}
 .bar{height:4px;border-radius:2px;background:linear-gradient(90deg,#2d7d46,#4ea1ff);display:inline-block;vertical-align:middle;margin-left:8px}
 a.gf{color:var(--accent);text-decoration:none}a.gf:hover{text-decoration:underline}
 .leaflet-container{background:#0d1117}
 .map-tip{background:#1a2029;border:1px solid #2b3340;border-radius:7px;padding:0;min-width:180px;box-shadow:0 4px 16px rgba(0,0,0,.6);color:#e6edf3;font:12px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
 .map-tip .tip-head{padding:5px 10px 4px;font-weight:700;font-size:13px;border-bottom:1px solid #2b3340}
 .map-tip .tip-weather{padding:3px 10px 4px;border-bottom:1px solid #2b3340;font-size:11px;color:#8b98a8}
 .map-tip .tip-flight{padding:3px 10px;border-bottom:1px solid #1e2630}
 .map-tip .tip-flight:last-child{border-bottom:none;padding-bottom:5px}
 .map-tip .tip-price{color:#7ee2a8;font-weight:700}
 .map-tip .tip-meta{color:#8b98a8;font-size:11px}
 .leaflet-tooltip{background:transparent;border:none;box-shadow:none;padding:0}
 .leaflet-tooltip-left:before,.leaflet-tooltip-right:before,.leaflet-tooltip-top:before,.leaflet-tooltip-bottom:before{border:none}
 .weather-legend{background:#1a2029;border:1px solid #2b3340;border-radius:7px;padding:8px 12px;color:#e6edf3;font:12px/1.7 -apple-system,sans-serif;line-height:1.7}
 .weather-legend b{display:block;margin-bottom:2px;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#8b98a8}
</style></head><body>
<header><h1>Spring Break 2027 Flights — Tel Aviv → Europe</h1>
<div class="sub">Google Flights · &le; 3,000 NIS (~$1,000) · 5–10 nights · Mar 24 – Apr 2, 2027 · captured __CAPTURE__ · <span id="total"></span> options · 3 NIS ≈ $1 USD. Click a column to sort; filter below.</div></header>
<div class="controls">
 <div class="ctrl"><label>Search</label><input id="search" placeholder="city / country / airline…"></div>
 <div class="ctrl"><label>Country</label><select id="fCountry"></select></div>
 <div class="ctrl"><label>Destination</label><select id="fDest"></select></div>
 <div class="ctrl"><label>Airline</label><select id="fAir"></select></div>
 <div class="ctrl"><label>Depart day</label><select id="fFrom"></select></div>
 <div class="ctrl"><label>Return day</label><select id="fTo"></select></div>
 <div class="ctrl"><label>Nights</label><div class="range"><input type="number" id="nMin" placeholder="min"><span>–</span><input type="number" id="nMax" placeholder="max"></div></div>
 <div class="ctrl"><label>Price (NIS)</label><div class="range"><input type="number" id="pMin" placeholder="min"><span>–</span><input type="number" id="pMax" placeholder="max"></div></div>
 <div class="ctrl"><label>Max flight (min)</label><input type="number" id="dMax" placeholder="e.g. 240"></div>
 <div class="ctrl"><label>Min Apr high (°C)</label><input type="number" id="tMin" placeholder="e.g. 18"></div>
 <div class="ctrl"><label>Max rain days</label><input type="number" id="rMax" placeholder="e.g. 8"></div>
 <div class="ctrl"><label>&nbsp;</label><button class="secondary" id="reset">Reset</button></div>
</div>
<div id="map"></div>
<div class="count" id="count"></div>
<div class="wrap"><table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA=__DATA__;const maxPrice=Math.max(...DATA.map(d=>d.price));
const cols=[
  {key:'dest',label:'Destination'},
  {key:'country',label:'Country'},
  {key:'price',label:'Price (NIS)',num:1},
  {key:'airline',label:'Airline'},
  {key:'from',label:'Depart',sortKey:'fromISO'},
  {key:'to',label:'Return',sortKey:'toISO'},
  {key:'nights',label:'Nights',num:1},
  {key:'length',label:'Flight length',sortKey:'durMin'},
  {key:'tempHigh',label:'Apr High/Low',num:1},
  {key:'rainDays',label:'Apr Rain',num:1},
  {key:'gf',label:'',nosort:1}
];
let sortKey='price',sortDir=1;
const uniq=k=>[...new Set(DATA.map(d=>d[k]))];
function fill(s,v,st){document.getElementById(s).innerHTML='<option value="">All</option>'+v.sort(st).map(x=>`<option>${x}</option>`).join('')}
fill('fCountry',uniq('country'),(a,b)=>a.localeCompare(b));
fill('fDest',uniq('dest'),(a,b)=>a.localeCompare(b));
fill('fAir',uniq('airline'),(a,b)=>a.localeCompare(b));
fill('fFrom',uniq('from'),(a,b)=>DATA.find(d=>d.from==a).fromISO.localeCompare(DATA.find(d=>d.from==b).fromISO));
fill('fTo',uniq('to'),(a,b)=>DATA.find(d=>d.to==a).toISO.localeCompare(DATA.find(d=>d.to==b).toISO));
document.getElementById('total').textContent=DATA.length;
const head=document.getElementById('head');
function renderHead(){head.innerHTML=cols.map(c=>{if(c.nosort)return'<th></th>';const k=c.sortKey||c.key;const a=(sortKey===k)?` <span class="arrow">${sortDir>0?'▲':'▼'}</span>`:'';return`<th data-k="${k}">${c.label}${a}</th>`}).join('');head.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=1}render()})}
const gf=d=>'https://www.google.com/travel/flights?q='+encodeURIComponent('Flights from Tel Aviv to '+d.dest+' on '+d.fromISO+' returning '+d.toISO);
const val=id=>document.getElementById(id).value.trim();const num=id=>{const v=document.getElementById(id).value;return v===''?null:Number(v)};
function weatherColor(high,rain){
  if(high===null||high===undefined)return'#4ea1ff';
  const t=Math.min(1,Math.max(0,(high-10)/14));
  const r=Math.min(1,Math.max(0,1-(rain-4)/11));
  const s=t*0.6+r*0.4;
  if(s>=0.75)return'#ff9944';
  if(s>=0.55)return'#ffcc44';
  if(s>=0.35)return'#88cc77';
  return'#5588bb';
}
function filtered(){
  const q=val('search').toLowerCase(),fc=val('fCountry'),fd=val('fDest'),fa=val('fAir'),ff=val('fFrom'),ft=val('fTo'),
    nmin=num('nMin'),nmax=num('nMax'),pmin=num('pMin'),pmax=num('pMax'),dmax=num('dMax'),tmin=num('tMin'),rmax=num('rMax');
  return DATA.filter(d=>{
    if(q&&!(d.dest.toLowerCase().includes(q)||d.country.toLowerCase().includes(q)||d.airline.toLowerCase().includes(q)))return false;
    if(fc&&d.country!==fc)return false;if(fd&&d.dest!==fd)return false;if(fa&&d.airline!==fa)return false;
    if(ff&&d.from!==ff)return false;if(ft&&d.to!==ft)return false;
    if(nmin!=null&&d.nights<nmin)return false;if(nmax!=null&&d.nights>nmax)return false;
    if(pmin!=null&&d.price<pmin)return false;if(pmax!=null&&d.price>pmax)return false;
    if(dmax!=null&&d.durMin>dmax)return false;
    if(tmin!=null&&(d.tempHigh===null||d.tempHigh<tmin))return false;
    if(rmax!=null&&(d.rainDays===null||d.rainDays>rmax))return false;
    return true;
  });
}

// --- Map ---
const COORDS={'Athens':[37.984,23.728],'Barcelona':[41.385,2.173],'Berlin':[52.520,13.405],
 'Catania':[37.508,15.083],'Chania':[35.514,24.018],'Corfu':[39.624,19.922],
 'Dubrovnik':[42.651,18.094],'Dusseldorf':[51.222,6.776],'Hamburg':[53.575,10.015],
 'Heraklion':[35.339,25.144],'Kos':[36.894,27.288],'Madrid':[40.417,-3.704],
 'Milan':[45.465,9.186],'Milan Bergamo':[45.674,9.704],'Munich':[48.135,11.582],
 'Mykonos':[37.447,25.329],'Naples':[40.852,14.268],'Palermo':[38.116,13.362],
 'Rhodes':[36.434,28.218],'Rome':[41.903,12.496],'Santorini':[36.393,25.461],
 'Thessaloniki':[40.640,22.944],'Venice':[45.441,12.316],'Split':[43.508,16.440],
 'Zagreb':[45.815,15.982],'Zadar':[44.120,15.230],'Pula':[44.868,13.848],
 'Vienna':[48.208,16.374],'Salzburg':[47.800,13.045],'Innsbruck':[47.269,11.404],'Graz':[47.070,15.440],
 'Paris':[48.857,2.352],'Paris Orly':[48.726,2.365],'Nice':[43.710,7.262],'Prague':[50.075,14.437],
 'Zurich':[47.376,8.541],'Geneva':[46.204,6.143],'Budapest':[47.498,19.040],
 'Amsterdam':[52.370,4.895],'Eindhoven':[51.441,5.478],'Rotterdam':[51.923,4.469],
 'London':[51.505,-0.090],'London Gatwick':[51.156,-0.161],'London Stansted':[51.885,0.235],'London Luton':[51.879,-0.374],
 'Manchester':[53.480,-2.242],'Edinburgh':[55.953,-3.188],
 'Brussels':[50.846,4.352],'Brussels Charleroi':[50.460,4.453],
 'Marseille':[43.296,5.381],'Lyon':[45.750,4.845],'Bordeaux':[44.837,-0.579],
 'Lisbon':[38.717,-9.139],'Porto':[41.149,-8.610],'Faro':[37.019,-7.930],
 'Copenhagen':[55.676,12.568],'Ljubljana':[46.051,14.506],
 'Malaga':[36.720,-4.420],'Valencia':[39.470,-0.376],'Palma':[39.570,2.650],
 'Alicante':[38.345,-0.481],'Ibiza':[38.909,1.433],'Seville':[37.389,-5.984],
 'Bari':[41.117,16.872],'Bologna':[44.494,11.343],'Cagliari':[39.215,9.110],
 'Brindisi':[40.632,17.947],'Verona':[45.439,10.993],'Turin':[45.070,7.687],
 'Pisa':[43.722,10.401],'Venice Treviso':[45.648,12.194],
 'Corfu':[39.624,19.922],'Zakynthos':[37.779,20.899],'Skiathos':[39.177,23.504],'Preveza':[38.950,20.766]};

const map=L.map('map',{zoomControl:true,attributionControl:false}).setView([43,18],4);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{maxZoom:18,subdomains:'abcd'}).addTo(map);

const legend=L.control({position:'bottomright'});
legend.onAdd=()=>{
  const div=L.DomUtil.create('div','weather-legend');
  div.innerHTML='<b>Apr weather</b>'+
    '<div><span style="color:#ff9944;font-size:16px">●</span> Warm &amp; dry</div>'+
    '<div><span style="color:#ffcc44;font-size:16px">●</span> Mild</div>'+
    '<div><span style="color:#88cc77;font-size:16px">●</span> Moderate</div>'+
    '<div><span style="color:#5588bb;font-size:16px">●</span> Cool / wet</div>';
  return div;
};
legend.addTo(map);

let mapMarkers=[];
function renderMap(){
  mapMarkers.forEach(m=>map.removeLayer(m));mapMarkers=[];
  const rows=filtered();
  const byDest={};
  rows.forEach(d=>{if(!byDest[d.dest])byDest[d.dest]=[];byDest[d.dest].push(d)});
  Object.values(byDest).forEach(arr=>arr.sort((a,b)=>a.price-b.price));
  const top10=Object.entries(byDest).sort((a,b)=>a[1][0].price-b[1][0].price).slice(0,10);
  top10.forEach(([dest,flights],rank)=>{
    const coords=COORDS[dest];if(!coords)return;
    const top3=flights.slice(0,3);
    const f0=flights[0];
    const wColor=weatherColor(f0.tempHigh,f0.rainDays);
    const weatherLine=f0.tempHigh!==null
      ?`<div class="tip-weather">☀ ${f0.tempHigh}° / ${f0.tempLow}° &nbsp;·&nbsp; 🌧 ${f0.rainDays} rain days</div>`:'';
    const tipHtml='<div class="map-tip"><div class="tip-head">'+dest+'</div>'+weatherLine+
      top3.map(f=>'<div class="tip-flight"><span class="tip-price">₪'+f.price.toLocaleString()+'</span> · '+f.airline+
        '<div class="tip-meta">'+f.from+' → '+f.to+' · '+f.nights+' nights · '+f.length+'</div></div>').join('')+'</div>';
    const size=rank===0?14:rank<3?11:8;
    const marker=L.circleMarker(coords,{
      radius:size,fillColor:wColor,color:'#fff',weight:1.5,fillOpacity:rank===0?1:0.75,
    }).bindTooltip(tipHtml,{className:'',sticky:false,direction:'auto',offset:[0,0]}).addTo(map);
    mapMarkers.push(marker);
  });
}

function render(){
  renderHead();
  let rows=filtered();
  rows.sort((a,b)=>{
    let x=a[sortKey],y=b[sortKey];
    if(x===null||x===undefined)x=sortDir>0?Infinity:-Infinity;
    if(y===null||y===undefined)y=sortDir>0?Infinity:-Infinity;
    if(typeof x==='string'){x=x.toLowerCase();y=y.toLowerCase();return x<y?-1*sortDir:x>y?1*sortDir:0}
    return(x-y)*sortDir;
  });
  document.getElementById('body').innerHTML=rows.map(d=>{
    const w=Math.round(d.price/maxPrice*60);
    const wc=weatherColor(d.tempHigh,d.rainDays);
    const tempStr=d.tempHigh!==null?`${d.tempHigh}° / ${d.tempLow}°`:'—';
    const rainStr=d.rainDays!==null?`${d.rainDays} days`:'—';
    return`<tr><td>${d.dest}</td><td class="country">${d.country}</td><td class="num price">₪${d.price.toLocaleString()}<span class="bar" style="width:${w}px"></span></td><td>${d.airline}</td><td>${d.from}</td><td>${d.to}</td><td class="num"><span class="pill">${d.nights}</span></td><td>${d.length}</td><td class="num" style="color:${wc}">${tempStr}</td><td class="num">${rainStr}</td><td><a class="gf" href="${gf(d)}" target="_blank" rel="noopener">open ↗</a></td></tr>`;
  }).join('');
  const ch=rows.length?Math.min(...rows.map(r=>r.price)):0;
  document.getElementById('count').textContent=`${rows.length} of ${DATA.length} flights`+(rows.length?` · cheapest ₪${ch.toLocaleString()}`:'');
  renderMap();
}
const ids=['search','fCountry','fDest','fAir','fFrom','fTo','nMin','nMax','pMin','pMax','dMax','tMin','rMax'];
ids.forEach(id=>{document.getElementById(id).addEventListener('input',render);document.getElementById(id).addEventListener('change',render)});
document.getElementById('reset').onclick=()=>{ids.forEach(id=>document.getElementById(id).value='');sortKey='price';sortDir=1;render()};
render();
</script></body></html>'''
HTML = HTML.replace("__DATA__", data_json).replace("__CAPTURE__", CAPTURE)
open("spring.html","w").write(HTML)
open("spring_index.html","w").write(HTML)
print(f"rows={nrows} dates={ndates} countries={countries}")
print("wrote spring.html, spring_index.html")
