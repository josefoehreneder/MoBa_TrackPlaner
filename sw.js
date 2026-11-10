/* Service Worker – Spur-N Gleisplaner */
const VERSION='gp-63aad416';
const SHELL=['./','index.html','manifest.webmanifest','icons/icon-192.png','icons/icon-512.png','icons/maskable-512.png','icons/apple-touch-icon.png','icons/favicon-64.png'];
const CDN=['https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js','https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'];
const EXT=/^https:\/\/(cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net|fonts\.googleapis\.com|fonts\.gstatic\.com)\//;

self.addEventListener('install',e=>{
  e.waitUntil((async()=>{
    const c=await caches.open(VERSION);
    await c.addAll(SHELL);
    // 3D-Bibliothek gleich mitnehmen, damit 3D auch offline geht (Fehler ignorieren)
    await Promise.all(CDN.map(u=>fetch(u,{mode:'cors'}).then(r=>r.ok&&c.put(u,r)).catch(()=>{})));
  })());
});
self.addEventListener('activate',e=>{
  e.waitUntil((async()=>{
    for(const k of await caches.keys())if(k!==VERSION)await caches.delete(k);
    await self.clients.claim();
  })());
});
self.addEventListener('message',e=>{if(e.data==='skipWaiting')self.skipWaiting()});
self.addEventListener('fetch',e=>{
  const req=e.request;if(req.method!=='GET')return;
  const url=new URL(req.url);
  // App-Seite: erst Cache, im Hintergrund aktualisieren
  if(req.mode==='navigate'){
    e.respondWith((async()=>{const c=await caches.open(VERSION);
      const hit=await c.match('index.html');
      const net=fetch(req).then(r=>{if(r.ok)c.put('index.html',r.clone());return r}).catch(()=>null);
      return hit||(await net)||new Response('Offline',{status:503});
    })());return;
  }
  if(url.origin===location.origin||EXT.test(req.url)){
    e.respondWith((async()=>{const c=await caches.open(VERSION);
      const hit=await c.match(req,{ignoreSearch:url.origin===location.origin});
      const net=fetch(req).then(r=>{if(r&&(r.ok||r.type==='opaque'))c.put(req,r.clone());return r}).catch(()=>null);
      return hit||(await net)||new Response('',{status:504});
    })());
  }
});
