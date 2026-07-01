#!/usr/bin/env python3
"""Build flights.html / index.html and the MD flight tables from serp_results.json."""
import json, datetime

DATA = json.load(open("serp_results.json"))
CAPTURE = datetime.date.today().isoformat()

def fmt_dur(mins):
    if not mins: return ""
    h, m = divmod(int(mins), 60)
    return (f"{h} hr" + (f" {m} min" if m else "")) if h else f"{m} min"

def fmt_date(iso):
    d = datetime.date.fromisoformat(iso); return d.strftime("%b ") + str(d.day)

rows = []
for key, dp in DATA.items():
    for f in dp["flights"]:
        rows.append({
            "dest": f["city"], "country": f["country"], "airport": f["airport"],
            "price": f["price"], "airline": f["airline"],
            "from": fmt_date(dp["dep"]), "to": fmt_date(dp["ret"]),
            "fromDay": datetime.date.fromisoformat(dp["dep"]).day,
            "toDay": datetime.date.fromisoformat(dp["ret"]).day,
            "nights": dp["nights"], "length": fmt_dur(f["dur"]), "durMin": f["dur"] or 0,
        })

ndates = len(DATA); nrows = len(rows)
countries = sorted(set(r["country"] for r in rows))
# cheapest per destination city
best = {}
for r in rows:
    if r["dest"] not in best or r["price"] < best[r["dest"]]["price"]:
        best[r["dest"]] = r

# ---------- Markdown ----------
md = []
md.append("## Flight Results (El Al · inspireme.elal.com)\n")
md.append(f"> Source: El Al InspireMe, captured {CAPTURE}. "
          f"Filters: from TLV, round-trip, El Al only, **≤ $850 USD** (prices shown in NIS at ~3.65 rate).\n"
          f"> Scope: all El Al destinations, **5–9 nights**, Aug 9–26 2026. {nrows} options across {ndates} date pairs.\n")
md.append("### Cheapest fare per destination\n")
md.append("| Destination | Country | Price (NIS) | Airline | From | To | Nights | Flight length |")
md.append("|---|---|---|---|---|---|---|---|")
for r in sorted(best.values(), key=lambda x:x["price"]):
    md.append(f"| {r['dest']} | {r['country']} | ₪{r['price']:,} | {r['airline']} | {r['from']} | {r['to']} | {r['nights']} | {r['length']} |")
md.append("\n## All Date Pairs — Full Flight List\n")
for key, dp in DATA.items():
    fl = sorted(dp["flights"], key=lambda x:x["price"])
    md.append(f"### {fmt_date(dp['dep'])} → {fmt_date(dp['ret'])} ({dp['nights']} nights) — {len(fl)} flights")
    md.append("| Destination | Country | Price (NIS) | Airline | From | To | Nights | Flight length |")
    md.append("|---|---|---|---|---|---|---|---|")
    for f in fl:
        md.append(f"| {f['city']} | {f['country']} | ₪{f['price']:,} | {f['airline']} | "
                  f"{fmt_date(dp['dep'])} | {fmt_date(dp['ret'])} | {dp['nights']} | {fmt_dur(f['dur'])} |")
    md.append("")
MD_SECTION = "\n".join(md)
open("flight_tables_serp.md","w").write(MD_SECTION)

# ---------- HTML ----------
data_json = json.dumps(rows, ensure_ascii=False)
HTML = r'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Summer 2026 Flights — TLV → Europe</title>
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
 #map{height:360px;border-bottom:1px solid var(--line)}
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
 .map-tip .tip-flight{padding:3px 10px;border-bottom:1px solid #1e2630}
 .map-tip .tip-flight:last-child{border-bottom:none;padding-bottom:5px}
 .map-tip .tip-price{color:#7ee2a8;font-weight:700}
 .map-tip .tip-meta{color:#8b98a8;font-size:11px}
 .leaflet-tooltip{background:transparent;border:none;box-shadow:none;padding:0}
 .leaflet-tooltip-left:before,.leaflet-tooltip-right:before,.leaflet-tooltip-top:before,.leaflet-tooltip-bottom:before{border:none}
</style></head><body>
<header><h1>Summer 2026 Flights — Tel Aviv → Europe</h1>
<div class="sub">El Al only · &le; $850 USD · 5–9 nights · Aug 9–26, 2026 · captured __CAPTURE__ · <span id="total"></span> options. Prices in NIS (~3.65 rate). Click a column to sort; filter below.</div></header>
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
 <div class="ctrl"><label>&nbsp;</label><button class="secondary" id="reset">Reset</button></div>
</div>
<div id="map"></div>
<div class="count" id="count"></div>
<div class="wrap"><table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA=__DATA__;const maxPrice=Math.max(...DATA.map(d=>d.price));
const cols=[{key:'dest',label:'Destination'},{key:'country',label:'Country'},{key:'price',label:'Price (NIS)',num:1},{key:'airline',label:'Airline'},{key:'from',label:'Depart',sortKey:'fromDay'},{key:'to',label:'Return',sortKey:'toDay'},{key:'nights',label:'Nights',num:1},{key:'length',label:'Flight length',sortKey:'durMin'},{key:'gf',label:'',nosort:1}];
let sortKey='price',sortDir=1;
const uniq=k=>[...new Set(DATA.map(d=>d[k]))];
function fill(s,v,st){document.getElementById(s).innerHTML='<option value="">All</option>'+v.sort(st).map(x=>`<option>${x}</option>`).join('')}
fill('fCountry',uniq('country'),(a,b)=>a.localeCompare(b));fill('fDest',uniq('dest'),(a,b)=>a.localeCompare(b));fill('fAir',uniq('airline'),(a,b)=>a.localeCompare(b));
fill('fFrom',uniq('from'),(a,b)=>DATA.find(d=>d.from==a).fromDay-DATA.find(d=>d.from==b).fromDay);
fill('fTo',uniq('to'),(a,b)=>DATA.find(d=>d.to==a).toDay-DATA.find(d=>d.to==b).toDay);
document.getElementById('total').textContent=DATA.length;
const head=document.getElementById('head');
function renderHead(){head.innerHTML=cols.map(c=>{if(c.nosort)return'<th></th>';const k=c.sortKey||c.key;const a=(sortKey===k)?` <span class="arrow">${sortDir>0?'▲':'▼'}</span>`:'';return`<th data-k="${k}">${c.label}${a}</th>`}).join('');head.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=1}render()})}
const gf=d=>'https://www.google.com/travel/flights?q='+encodeURIComponent('Flights from Tel Aviv to '+d.dest+' on 2026-08-'+String(d.fromDay).padStart(2,'0')+' returning 2026-08-'+String(d.toDay).padStart(2,'0'));
const val=id=>document.getElementById(id).value.trim();const num=id=>{const v=document.getElementById(id).value;return v===''?null:Number(v)};
function filtered(){const q=val('search').toLowerCase(),fc=val('fCountry'),fd=val('fDest'),fa=val('fAir'),ff=val('fFrom'),ft=val('fTo'),nmin=num('nMin'),nmax=num('nMax'),pmin=num('pMin'),pmax=num('pMax'),dmax=num('dMax');
 return DATA.filter(d=>{if(q&&!(d.dest.toLowerCase().includes(q)||d.country.toLowerCase().includes(q)||d.airline.toLowerCase().includes(q)))return false;if(fc&&d.country!==fc)return false;if(fd&&d.dest!==fd)return false;if(fa&&d.airline!==fa)return false;if(ff&&d.from!==ff)return false;if(ft&&d.to!==ft)return false;if(nmin!=null&&d.nights<nmin)return false;if(nmax!=null&&d.nights>nmax)return false;if(pmin!=null&&d.price<pmin)return false;if(pmax!=null&&d.price>pmax)return false;if(dmax!=null&&d.durMin>dmax)return false;return true})}

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
 'Paris':[48.857,2.352],'Nice':[43.710,7.262],'Prague':[50.075,14.437],'Zurich':[47.376,8.541],
 'Budapest':[47.498,19.040],'Amsterdam':[52.370,4.895],'Eindhoven':[51.441,5.478],
 'Sofia':[42.698,23.322],'Bucharest':[44.430,26.103],'Larnaca':[34.885,33.625],
 'Geneva':[46.204,6.143],'Tbilisi':[41.715,44.827],'Dubai':[25.204,55.270],
 'London':[51.505,-0.090],'Marseilles':[43.296,5.381],'Madrid':[40.417,-3.704]};

const map=L.map('map',{zoomControl:true,attributionControl:false}).setView([43,18],4);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{maxZoom:18,subdomains:'abcd'}).addTo(map);

let mapMarkers=[];
function renderMap(){
  mapMarkers.forEach(m=>map.removeLayer(m));
  mapMarkers=[];
  const rows=filtered();
  // group by dest, sort flights by price
  const byDest={};
  rows.forEach(d=>{if(!byDest[d.dest])byDest[d.dest]=[];byDest[d.dest].push(d)});
  Object.values(byDest).forEach(arr=>arr.sort((a,b)=>a.price-b.price));
  // top 10 cheapest destinations
  const top10=Object.entries(byDest)
    .sort((a,b)=>a[1][0].price-b[1][0].price)
    .slice(0,10);
  top10.forEach(([dest,flights],rank)=>{
    const coords=COORDS[dest];if(!coords)return;
    const top3=flights.slice(0,3);
    const tipHtml='<div class="map-tip"><div class="tip-head">'+dest+'</div>'+
      top3.map(f=>'<div class="tip-flight"><span class="tip-price">₪'+f.price.toLocaleString()+'</span> · '+f.airline+
        '<div class="tip-meta">'+f.from+' → '+f.to+' · '+f.nights+' nights · '+f.length+'</div></div>').join('')+'</div>';
    const size=rank===0?14:rank<3?11:8;
    const marker=L.circleMarker(coords,{
      radius:size,fillColor:'#4ea1ff',color:'#fff',weight:1.5,fillOpacity:rank===0?1:0.75,
    }).bindTooltip(tipHtml,{className:'',sticky:false,direction:'auto',offset:[0,0]}).addTo(map);
    mapMarkers.push(marker);
  });
}

function render(){renderHead();let rows=filtered();rows.sort((a,b)=>{let x=a[sortKey],y=b[sortKey];if(typeof x==='string'){x=x.toLowerCase();y=y.toLowerCase();return x<y?-1*sortDir:x>y?1*sortDir:0}return(x-y)*sortDir});
 document.getElementById('body').innerHTML=rows.map(d=>{const w=Math.round(d.price/maxPrice*60);return`<tr><td>${d.dest}</td><td class="country">${d.country}</td><td class="num price">₪${d.price.toLocaleString()}<span class="bar" style="width:${w}px"></span></td><td>${d.airline}</td><td>${d.from}</td><td>${d.to}</td><td class="num"><span class="pill">${d.nights}</span></td><td>${d.length}</td><td><a class="gf" href="${gf(d)}" target="_blank" rel="noopener">open ↗</a></td></tr>`}).join('');
 const ch=rows.length?Math.min(...rows.map(r=>r.price)):0;document.getElementById('count').textContent=`${rows.length} of ${DATA.length} flights`+(rows.length?` · cheapest ₪${ch.toLocaleString()}`:'');
 renderMap();}
const ids=['search','fCountry','fDest','fAir','fFrom','fTo','nMin','nMax','pMin','pMax','dMax'];
ids.forEach(id=>{document.getElementById(id).addEventListener('input',render);document.getElementById(id).addEventListener('change',render)});
document.getElementById('reset').onclick=()=>{ids.forEach(id=>document.getElementById(id).value='');sortKey='price';sortDir=1;render()};
render();
</script></body></html>'''
HTML = HTML.replace("__DATA__", data_json).replace("__CAPTURE__", CAPTURE)
open("flights.html","w").write(HTML)
open("index.html","w").write(HTML)
print(f"rows={nrows} dates={ndates} countries={countries}")
print("wrote flights.html, index.html, flight_tables_serp.md")
