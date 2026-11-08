// Guarda o guia inteiro no celular para funcionar sem internet.
var VERSAO = "roma-ca5a36c995";
var ARQUIVOS = [
"./",
"app.css",
"app.js",
"fonts/Lora-400.ttf",
"fonts/Lora-500.ttf",
"fonts/Lora-600.ttf",
"fonts/Lora-700.ttf",
"fonts/Lora-Italic.ttf",
"fonts/Lora-MediumItalic.ttf",
"fonts/Poppins-Light.ttf",
"fonts/Poppins-Medium.ttf",
"fonts/Poppins-Regular.ttf",
"fotos/apolo-sosiano-reconstrucao.jpg",
"fotos/apolo-sosiano.jpg",
"fotos/arco-jano.jpg",
"fotos/argentina-vista-norte.jpg",
"fotos/basilica.jpg",
"fotos/bencao-natal.jpg",
"fotos/bocca-verita.jpg",
"fotos/borghese-paolina.jpg",
"fotos/borghese-proserpina.jpg",
"fotos/borghese-salao.jpg",
"fotos/borgo-pio.jpg",
"fotos/case-romane-celio.jpg",
"fotos/castel-santangelo.jpg",
"fotos/circo-maximo-reconstrucao.jpg",
"fotos/circo-maximo.jpg",
"fotos/coliseu-arena.jpg",
"fotos/coliseu.jpg",
"fotos/colonna-afresco.jpg",
"fotos/colonna-paisagens.jpg",
"fotos/colonna-salao.jpg",
"fotos/curia-pompeu.jpg",
"fotos/embaixada-brasil.jpg",
"fotos/estadio-reconstrucao.jpg",
"fotos/forum-romano.jpg",
"fotos/largo-argentina.jpg",
"fotos/mamertino-altar.jpg",
"fotos/mamertino-coluna.jpg",
"fotos/mamertino-fachada.jpg",
"fotos/mercato-testaccio.jpg",
"fotos/minerva1.jpg",
"fotos/minerva2.jpg",
"fotos/minerva3.jpg",
"fotos/monte-testaccio.jpg",
"fotos/moro.jpg",
"fotos/museus-vaticanos.jpg",
"fotos/navona1.jpg",
"fotos/navona2.jpg",
"fotos/navona3.jpg",
"fotos/navona4.jpg",
"fotos/nettuno.jpg",
"fotos/pantheon.jpg",
"fotos/piazza-liberta.jpg",
"fotos/piazza-popolo.jpg",
"fotos/piazza-spagna2.jpg",
"fotos/piazza-venezia.jpg",
"fotos/planta-area-sacra.jpg",
"fotos/portico-ottavia.jpg",
"fotos/praca-sao-pedro.jpg",
"fotos/priscila-virgem.jpg",
"fotos/quatro-fiumi.jpg",
"fotos/rosso.jpg",
"fotos/santa-maria-maggiore.jpg",
"fotos/sao-joao-latrao.jpg",
"fotos/scavi.jpg",
"fotos/teatro-marcello.jpg",
"fotos/templo-a.jpg",
"fotos/templo-b.jpg",
"fotos/templo-c.jpg",
"fotos/templo-hercules.jpg",
"fotos/templo-portuno.jpg",
"fotos/torre-papito.jpg",
"fotos/trastevere.jpg",
"fotos/via-del-corso.jpg",
"fotos/villa-borghese.jpg",
"fotos/volpetti.jpg",
"icons/apple-touch-icon.png",
"icons/icon-192.png",
"icons/icon-512.png",
"icons/maskable-512.png",
"index.html",
"manifest.webmanifest"
];

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
