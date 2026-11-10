#!/usr/bin/env python3
"""Baut die installierbare App (PWA) aus spur-n-gleisplaner.html.
Aufruf:  python3 tools/build.py   (im Hauptordner des Repositorys)
Quelle:  tools/spur-n-gleisplaner.html  ->  Ausgabe im Hauptordner
"""
import json, pathlib, re, hashlib

TOOLS = pathlib.Path(__file__).resolve().parent
HERE = TOOLS.parent
SRC = TOOLS / 'spur-n-gleisplaner.html'
src = SRC.read_text(encoding='utf-8')

# Versionsnummer aus dem Inhalt, damit der Service Worker Updates erkennt
VERSION = hashlib.sha1(src.encode()).hexdigest()[:8]

# Kopfbereich des Artifacts (title, meta, fonts) durch vollständigen <head> ersetzen
body_start = src.index('<style>')
style_end = src.index('</style>') + len('</style>')
style = src[body_start:style_end]
rest = src[style_end:]

HEAD = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<title>Spur-N Gleisplaner</title>
<meta name="description" content="Gleispläne für Spur N planen – Kato, Minitrix, Fleischmann piccolo, Peco – mit Steigungen und 2D/3D-Ansicht.">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1A201D" media="(prefers-color-scheme: dark)">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Gleisplaner">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="icons/favicon-64.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap">
<style>
/* Grundgerüst (entspricht dem Artifact-Rahmen) */
:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px system-ui,-apple-system,"Segoe UI",sans-serif}}
img{{max-width:100%}}
[hidden]{{display:none!important}}
/* App-Ergänzungen */
.install-row{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.ios-hint{{background:var(--accent-soft);border:1px solid var(--accent);border-radius:10px;padding:10px 12px;color:var(--ink);line-height:1.45;font-size:13.5px}}
#instBar{{position:fixed;left:max(12px,env(safe-area-inset-left,0px));right:max(12px,env(safe-area-inset-right,0px));top:calc(10px + env(safe-area-inset-top,0px));z-index:40;display:flex;gap:10px;align-items:center;background:var(--ink);color:var(--bg);padding:10px 10px 10px 12px;border-radius:14px;box-shadow:0 6px 24px rgba(0,0,0,.3);max-width:560px;margin:0 auto}}
#instBar img{{width:40px;height:40px;border-radius:9px;flex:none}}
#instBar .t{{flex:1;min-width:0;line-height:1.3}}
#instBar .t>b{{display:block;font-size:14.5px}}
#instBar .t span{{font-size:12.5px;opacity:.8}}
#instBar button{{border:0;border-radius:10px;font-weight:600;min-height:38px;padding:0 14px;flex:none}}
#instGo{{background:var(--accent);color:var(--accent-ink)}}
#instX{{background:transparent;color:var(--bg);font-size:18px;padding:0 8px!important}}
#instBtnTop{{display:none}}
#instBtnTop.show{{display:inline-flex;align-items:center}}
#updBar{{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(14px + env(safe-area-inset-bottom,0px));z-index:30;display:flex;gap:10px;align-items:center;background:var(--ink);color:var(--bg);padding:8px 8px 8px 14px;border-radius:999px;box-shadow:0 4px 16px rgba(0,0,0,.25);font-size:13.5px;max-width:calc(100% - 32px)}}
#updBar button{{border:0;border-radius:999px;background:var(--accent);color:var(--accent-ink);font-weight:600;padding:6px 12px;min-height:34px}}
</style>
'''

PWA_JS = r'''
<div id="instBar" hidden role="dialog" aria-label="App installieren">
  <img src="icons/icon-192.png" alt="">
  <div class="t"><b>Gleisplaner als App</b><span id="instTxt">Auf den Startbildschirm legen – läuft dann im Vollbild und offline.</span></div>
  <button id="instGo">Installieren</button><button id="instX" aria-label="Später">✕</button>
</div>
<div id="updBar" hidden><span>Neue Version verfügbar</span><button id="updBtn">Neu laden</button></div>
<input id="planFile" type="file" accept=".json,.gleisplan,application/json" hidden>
<script>
(()=>{
'use strict';
const isStandalone=()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
const isIOS=/iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
let deferred=null;
const bar=document.getElementById('instBar'),go=document.getElementById('instGo'),txt=document.getElementById('instTxt');
const snoozed=()=>{try{return Date.now()<+(localStorage.getItem('gp.instSnooze')||0)}catch(e){return false}};
function showBar(){if(isStandalone()||snoozed())return;
  if(deferred){go.hidden=false;go.textContent='Installieren';txt.textContent='Auf den Startbildschirm legen – läuft dann im Vollbild und offline.'}
  else if(isIOS){go.hidden=true;txt.innerHTML='In Safari unten auf <b>Teilen</b> tippen, dann <b>Zum Home-Bildschirm</b>.'}
  else{go.hidden=true;txt.innerHTML='Im Browser-Menü <b>⋮</b> auf <b>App installieren</b> tippen.'}
  bar.hidden=false}
function doInstall(){if(!deferred){showBar();return}const d=deferred;deferred=null;bar.hidden=true;
  d.prompt();d.userChoice.then(c=>{if(c.outcome!=='accepted')upd()}).finally(upd)}
function upd(){const b=document.getElementById('instBtnTop');if(b)b.classList.toggle('show',!isStandalone()&&!!deferred)}
go.onclick=doInstall;
document.getElementById('instX').onclick=()=>{bar.hidden=true;try{localStorage.setItem('gp.instSnooze',String(Date.now()+3*24*3600e3))}catch(e){}};
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferred=e;upd();showBar()});
window.addEventListener('appinstalled',()=>{deferred=null;bar.hidden=true;upd();window.__plan&&__plan.toast('App installiert')});
// Ohne Installationsangebot des Browsers (iPhone, Firefox …) nach kurzer Zeit Anleitung zeigen
setTimeout(()=>{if(!deferred&&!isStandalone())showBar()},2500);
// Knopf in der Kopfzeile
(()=>{const h=document.querySelector('.top'),m=document.getElementById('menuBtn');if(!h||!m)return;
  const b=document.createElement('button');b.id='instBtnTop';b.className='btn primary';b.textContent='⤓ App';b.title='App installieren';
  b.onclick=doInstall;h.insertBefore(b,m)})();

// Service Worker
if('serviceWorker' in navigator&&location.protocol!=='file:'){
  window.addEventListener('load',()=>{
    navigator.serviceWorker.register('sw.js').then(reg=>{
      const show=w=>{if(!w)return;const bar=document.getElementById('updBar');bar.hidden=false;
        document.getElementById('updBtn').onclick=()=>{w.postMessage('skipWaiting')};};
      if(reg.waiting&&navigator.serviceWorker.controller)show(reg.waiting);
      reg.addEventListener('updatefound',()=>{const w=reg.installing;
        w&&w.addEventListener('statechange',()=>{if(w.state==='installed'&&navigator.serviceWorker.controller)show(w)})});
      setInterval(()=>reg.update().catch(()=>{}),60*60*1000);
    }).catch(()=>{});
    let reloaded=false;
    navigator.serviceWorker.addEventListener('controllerchange',()=>{if(reloaded)return;reloaded=true;location.reload()});
  });
}
// Plan dauerhaft speichern lassen (Browser löscht dann nicht so schnell)
try{navigator.storage&&navigator.storage.persist&&navigator.storage.persist()}catch(e){}

// Datei speichern / öffnen
function saveFile(){
  const txt=__plan.get(),d=new Date(),stamp=d.toISOString().slice(0,10);
  const name=`gleisplan-${stamp}.json`,blob=new Blob([txt],{type:'application/json'});
  const file=new File([blob],name,{type:'application/json'});
  if(navigator.canShare&&navigator.canShare({files:[file]})){
    navigator.share({files:[file],title:'Spur-N Gleisplan'}).catch(err=>{if(err&&err.name!=='AbortError')download()});
  }else download();
  function download(){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;
    document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},1000);__plan.toast('Plan gespeichert: '+name)}
}
const fi=document.getElementById('planFile');
fi.addEventListener('change',()=>{const f=fi.files&&fi.files[0];if(!f)return;
  f.text().then(t=>{try{__plan.load(t);__plan.toast('Plan geöffnet: '+f.name)}catch(e){__plan.toast('Die Datei ist kein gültiger Gleisplan')}}).finally(()=>{fi.value=''})});

// Bereich im Plan-Menü
window.__pwaSheet=()=>{
  const slot=document.getElementById('pwaSlot');if(!slot)return;
  let inst='';
  if(isStandalone())inst='<p>Die App ist installiert und läuft auch ohne Internet.</p>';
  else if(deferred)inst='<div class="install-row"><button class="btn primary" id="instBtn">App installieren</button></div><p>Legt den Gleisplaner als App auf den Startbildschirm. Danach läuft er im Vollbild und ohne Internet.</p>';
  else if(isIOS)inst='<div class="ios-hint">So installierst du die App auf dem iPhone: In Safari unten auf <b>Teilen</b> (Quadrat mit Pfeil) tippen, dann <b>Zum Home-Bildschirm</b>.</div>';
  else inst='<div class="ios-hint">Im Browser-Menü (⋮) auf <b>App installieren</b> oder <b>Zum Startbildschirm hinzufügen</b> tippen.</div>';
  slot.innerHTML=`<h3>App</h3>${inst}
    <h3>Datei</h3><div class="install-row"><button class="btn primary" id="fSave">Als Datei speichern</button><button class="btn" id="fOpen">Datei öffnen</button></div>
    <p>Speichert den Plan als .json-Datei, z. B. zum Sichern oder zum Weitergeben per WhatsApp oder Mail.</p>`;
  const ib=document.getElementById('instBtn');
  if(ib)ib.onclick=()=>{document.getElementById('sheet').hidden=true;doInstall()};
  document.getElementById('fSave').onclick=saveFile;
  document.getElementById('fOpen').onclick=()=>fi.click();
};
})();
</script>
'''

html = HEAD + style + '\n</head>\n<body>\n' + rest.strip() + '\n' + PWA_JS + '</body>\n</html>\n'
(HERE / 'index.html').write_text(html, encoding='utf-8')

manifest = {
  "name": "Spur-N Gleisplaner",
  "short_name": "Gleisplaner",
  "description": "Gleispläne für Spur N mit Steigungen, Weichen und 2D/3D-Ansicht.",
  "lang": "de",
  "id": "./",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "display_override": ["standalone", "minimal-ui"],
  "orientation": "any",
  "background_color": "#E9ECE7",
  "theme_color": "#1C2521",
  "categories": ["utilities", "productivity"],
  "icons": [
    {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
    {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
    {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
(HERE / 'manifest.webmanifest').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

VERSION = hashlib.sha1((src + HEAD + PWA_JS).encode()).hexdigest()[:8]
SW = f'''/* Service Worker – Spur-N Gleisplaner */
const VERSION='gp-{VERSION}';
const SHELL=['./','index.html','manifest.webmanifest','icons/icon-192.png','icons/icon-512.png','icons/maskable-512.png','icons/apple-touch-icon.png','icons/favicon-64.png'];
const CDN=['https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js','https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'];
const EXT=/^https:\\/\\/(cdnjs\\.cloudflare\\.com|cdn\\.jsdelivr\\.net|fonts\\.googleapis\\.com|fonts\\.gstatic\\.com)\\//;

self.addEventListener('install',e=>{{
  e.waitUntil((async()=>{{
    const c=await caches.open(VERSION);
    await c.addAll(SHELL);
    // 3D-Bibliothek gleich mitnehmen, damit 3D auch offline geht (Fehler ignorieren)
    await Promise.all(CDN.map(u=>fetch(u,{{mode:'cors'}}).then(r=>r.ok&&c.put(u,r)).catch(()=>{{}})));
  }})());
}});
self.addEventListener('activate',e=>{{
  e.waitUntil((async()=>{{
    for(const k of await caches.keys())if(k!==VERSION)await caches.delete(k);
    await self.clients.claim();
  }})());
}});
self.addEventListener('message',e=>{{if(e.data==='skipWaiting')self.skipWaiting()}});
self.addEventListener('fetch',e=>{{
  const req=e.request;if(req.method!=='GET')return;
  const url=new URL(req.url);
  // App-Seite: erst Cache, im Hintergrund aktualisieren
  if(req.mode==='navigate'){{
    e.respondWith((async()=>{{const c=await caches.open(VERSION);
      const hit=await c.match('index.html');
      const net=fetch(req).then(r=>{{if(r.ok)c.put('index.html',r.clone());return r}}).catch(()=>null);
      return hit||(await net)||new Response('Offline',{{status:503}});
    }})());return;
  }}
  if(url.origin===location.origin||EXT.test(req.url)){{
    e.respondWith((async()=>{{const c=await caches.open(VERSION);
      const hit=await c.match(req,{{ignoreSearch:url.origin===location.origin}});
      const net=fetch(req).then(r=>{{if(r&&(r.ok||r.type==='opaque'))c.put(req,r.clone());return r}}).catch(()=>null);
      return hit||(await net)||new Response('',{{status:504}});
    }})());
  }}
}});
'''
(HERE / 'sw.js').write_text(SW, encoding='utf-8')

(HERE / '.nojekyll').write_text('', encoding='utf-8')
print('gebaut, Version', VERSION)
