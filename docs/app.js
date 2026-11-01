(function () {
  var pos = {};            // posição de rolagem de cada tela, para voltar ao ponto exato
  var atual = null, porClique = false, hist = 0;

  function mostrar() {
    var id = (location.hash || "#inicio").slice(1) || "inicio";
    var pg = document.getElementById("p-" + id) || document.getElementById("p-inicio");
    if (atual) pos[atual.id] = window.scrollY;
    if (atual) atual.classList.remove("on");
    pg.classList.add("on"); atual = pg;
    document.body.classList.toggle("on-home", pg.id === "p-inicio");
    document.getElementById("titulo").textContent = pg.dataset.title || "Roma con Amore";
    document.title = pg.id === "p-inicio" ? "Roma con Amore" : pg.dataset.title + " · Roma con Amore";
    window.scrollTo(0, porClique ? 0 : (pos[pg.id] || 0));
    porClique = false;
  }

  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="#"]');
    if (a && a.getAttribute("href") !== "#") { porClique = true; hist++; }
  });
  document.getElementById("voltar").addEventListener("click", function () {
    if (hist > 0) { hist--; history.back(); } else { location.hash = "#inicio"; }
  });
  window.addEventListener("popstate", function () { if (!porClique && hist > 0) hist--; });
  window.addEventListener("hashchange", mostrar);
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  mostrar();

  // lista "Antes de partir": marcações guardadas neste aparelho
  document.querySelectorAll(".chk input").forEach(function (cb) {
    try { cb.checked = localStorage.getItem(cb.dataset.k) === "1"; } catch (e) {}
    cb.addEventListener("change", function () {
      try { localStorage.setItem(cb.dataset.k, cb.checked ? "1" : "0"); } catch (e) {}
    });
  });

  // botão "Hoje" durante a viagem
  var hoje = new Date(), ymd = hoje.getFullYear() + "-" + String(hoje.getMonth() + 1).padStart(2, "0") + "-" + String(hoje.getDate()).padStart(2, "0");
  var bt = document.getElementById("hoje");
  for (var id in (window.DATAS || {})) {
    if (window.DATAS[id] === ymd) {
      bt.href = "#" + id; bt.textContent = "Abrir o roteiro de hoje ›"; bt.hidden = false;
    }
  }

  // dica de instalação, só quando aberto no navegador (não como app)
  var standalone = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone;
  var tip = document.getElementById("instalar");
  if (!standalone && tip) {
    var ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    tip.innerHTML = ios
      ? "<b>Para usar como app:</b> toque em Compartilhar (o quadrado com a seta) e depois em “Adicionar à Tela de Início”."
      : "<b>Para usar como app:</b> abra o menu do navegador (⋮) e toque em “Instalar app” ou “Adicionar à tela inicial”.";
    tip.hidden = false;
  }

  // funciona sem internet depois da primeira abertura
  if ("serviceWorker" in navigator) {
    var tinha = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.register("sw.js").then(function (r) { r.update(); }).catch(function () {});
    navigator.serviceWorker.addEventListener("controllerchange", function () { if (tinha) location.reload(); });
  }
})();
