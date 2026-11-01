// Guarda o guia inteiro no celular para funcionar sem internet.
var VERSAO = "roma-__VERSAO__";
var ARQUIVOS = __ARQUIVOS__;

self.addEventListener("install", function (ev) {
  ev.waitUntil(caches.open(VERSAO).then(function (c) { return c.addAll(ARQUIVOS.map(function (u) { return new Request(u, { cache: "reload" }); })); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (ev) {
  ev.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== VERSAO; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

// Sempre usa a cópia guardada (abre na hora, com ou sem sinal). Quando há uma versão nova do guia,
// o navegador baixa este arquivo de novo, guarda tudo outra vez e o app recarrega sozinho.
self.addEventListener("fetch", function (ev) {
  var req = ev.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  if (req.mode === "navigate") {
    ev.respondWith(caches.match("./").then(function (r) { return r || fetch(req); }));
    return;
  }
  ev.respondWith(caches.match(req).then(function (r) { return r || fetch(req); }));
});
