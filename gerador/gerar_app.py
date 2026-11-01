"""Gera o app (site instalável, funciona offline) do guia 'Roma con Amore'.
Usa os mesmos arquivos do PDF: dias.json, locais.json, reservas.json, fotos/ e fonts/.
Uso: python3 gerar_app.py <pasta da fonte> <pasta de saída>
"""
import json, sys, os, shutil, hashlib, html, re
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
D = json.load(open(os.path.join(src, "dias.json"), encoding="utf-8"))
L = json.load(open(os.path.join(src, "locais.json"), encoding="utf-8"))
R = json.load(open(os.path.join(src, "reservas.json"), encoding="utf-8"))
ANO = 2026

def e(s): return html.escape(str(s or ""), quote=True)
def gmaps(q): return "https://www.google.com/maps/search/?api=1&query=" + quote(q)
def gimg(q): return "https://www.google.com/search?tbm=isch&q=" + quote(q)
def ext(url, inner, cls=""): return f'<a class="{cls}" href="{e(url)}" target="_blank" rel="noopener">{inner}</a>'
def go(dest, inner, cls=""): return f'<a class="{cls}" href="#{e(dest)}">{inner}</a>'

# ------------------------------------------------------------- saída
if os.path.isdir(out):
    for n in os.listdir(out):
        if n == ".git": continue
        p = os.path.join(out, n)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
os.makedirs(os.path.join(out, "fotos"), exist_ok=True)
os.makedirs(os.path.join(out, "fonts"), exist_ok=True)
os.makedirs(os.path.join(out, "icons"), exist_ok=True)
for f in os.listdir(os.path.join(src, "fonts")):
    shutil.copy(os.path.join(src, "fonts", f), os.path.join(out, "fonts", f))

FOTOS = {}
def foto(rel):
    """Copia a foto reduzida para o app e devolve (caminho, largura, altura), ou None."""
    if not rel: return None
    if rel in FOTOS: return FOTOS[rel]
    fp = rel if os.path.isabs(rel) else os.path.join(src, rel)
    if not os.path.exists(fp): FOTOS[rel] = None; return None
    im = Image.open(fp)
    if im.mode not in ("RGB", "L"): im = im.convert("RGB")
    if im.width > 1100: im = im.resize((1100, round(im.height * 1100 / im.width)), Image.LANCZOS)
    name = os.path.splitext(os.path.basename(fp))[0] + ".jpg"
    im.save(os.path.join(out, "fotos", name), "JPEG", quality=80, optimize=True, progressive=True)
    FOTOS[rel] = ("fotos/" + name, im.width, im.height)
    return FOTOS[rel]

def img(rel, cls="", alt=""):
    f = foto(rel)
    if not f: return ""
    return f'<img class="{cls}" src="{f[0]}" width="{f[1]}" height="{f[2]}" alt="{e(alt)}" loading="lazy">'

# ------------------------------------------------------------- referências (mesma lógica do PDF)
ref_dias = {}
for d in D["dias"]:
    for it in d["itens"]:
        if it.get("ref"):
            lst = ref_dias.setdefault(it["ref"], [])
            if d not in lst: lst.append(d)
res_by_ref = {}
for r in R["itens"]:
    if r.get("ref"): res_by_ref.setdefault(r["ref"], []).append(r)
link_dias = {}
for d in D["dias"]:
    for it in d["itens"]:
        if it.get("link") and d not in link_dias.setdefault(it["link"], []): link_dias[it["link"]].append(d)

def route_plan(d):
    home = D["hospedagem"]["endereco"]
    stops = [(home, None, False)]
    taxi = False
    for k, it in enumerate(d["itens"]):
        tit = it["titulo"].lower()
        if it.get("tipo") == "trajeto" and "casa" in tit and ("táxi" in tit or "caminhada" in tit):
            if stops[-1][0] != home:
                stops.append((home, k, "táxi" in tit))
            taxi = False; continue
        if it.get("tipo") == "trajeto" and "táxi" in tit:
            taxi = True; continue
        if it.get("tipo") == "casa" and k == 0:
            stops[0] = (home, k, False); continue
        p = L.get(it.get("ref"))
        if p and p.get("rota", True) and (p.get("mapa") or p.get("endereco")):
            q = p.get("mapa") or p["endereco"]
            if q == stops[-1][0]:
                stops[-1] = stops[-1][:1] + (stops[-1][1] if stops[-1][1] is not None else k,) + stops[-1][2:]
                continue
            stops.append((q, k, taxi)); taxi = False
    if len(stops) < 2:
        return [], ({stops[0][1]: "A"} if stops[0][1] is not None else {}), False
    n = len(stops)
    parts = [(0, n - 1)] if n <= 11 else [(0, (n - 1) // 2), ((n - 1) // 2, n - 1)]
    multi = len(parts) > 1
    letras, mapas = {}, []
    for pi, (i0, i1) in enumerate(parts):
        part = stops[i0:i1 + 1]
        u = ("https://www.google.com/maps/dir/?api=1&travelmode=walking"
             + "&origin=" + quote(part[0][0]) + "&destination=" + quote(part[-1][0]))
        if len(part) > 2: u += "&waypoints=" + quote("|".join(s[0] for s in part[1:-1]))
        mapas.append(u)
        for j, s in enumerate(part):
            lab = chr(65 + j)
            if multi: lab = f"{pi + 1}{lab}"
            if s[1] is not None and not (j == 0 and s[1] in letras):
                letras[s[1]] = lab
    return mapas, letras, multi

def leg_maps(d):
    home = D["hospedagem"]["endereco"]
    def loc(it):
        if it.get("tipo") == "casa": return home
        p = L.get(it.get("ref"))
        if p and (p.get("mapa") or p.get("endereco")): return p.get("mapa") or p["endereco"]
        return None
    res = {}; cur = home; its = d["itens"]
    for k, it in enumerate(its):
        tit = it["titulo"].lower()
        if (it.get("tipo") == "trajeto" or "casa" in tit) and "caminhada" in tit:
            dest = it.get("destino") or (home if "casa" in tit else next((loc(x) for x in its[k + 1:] if loc(x)), None))
            if dest and dest != cur:
                u = ("https://www.google.com/maps/dir/?api=1&travelmode=walking&origin=" + quote(cur)
                     + "&destination=" + quote(dest))
                if it.get("via"): u += "&waypoints=" + quote("|".join(it["via"]))
                res[k] = u
            if "casa" in tit: cur = home
            elif it.get("destino"): cur = it["destino"]
            continue
        if it.get("tipo") == "trajeto" and "táxi" in tit and "casa" in tit: cur = home; continue
        l = loc(it)
        if l: cur = l
    return res

STATUS = {"confirmado": ("sage", "Confirmado"), "reservar": ("wine", "A reservar"),
          "confirmar": ("gold", "A confirmar"), "comprar": ("wine", "A comprar"), "info": ("muted", "Informativo")}
def pill(key):
    cls, lab = STATUS.get(key, ("muted", key))
    return f'<span class="pill {cls}">{e(lab)}</span>'

def paras(txt, cls=""):
    return "".join(f'<p class="{cls}">{e(p)}</p>' for p in str(txt).split("\n") if p.strip())

PAGES = []   # (id, html, título curto)
def page(pid, body, title, cls=""):
    PAGES.append(f'<section class="pg {cls}" id="p-{e(pid)}" data-title="{e(title)}">{body}</section>')

def voltar_dia(dias):
    if not dias: return ""
    return '<div class="backdays">' + "".join(go(d["id"], f"‹ Dia {e(d['data'])}", "chip") for d in dias) + "</div>"

# ------------------------------------------------------------- início (capa + sumário)
rows = []
for i, d in enumerate(D["dias"]):
    rows.append(go(d["id"], f'<span class="num">{e(d["data"][:2])}</span>'
                 f'<span class="txt"><span class="kick muted">Dia {i + 1} · {e(d["semana"])}</span>'
                 f'<span class="tt">{e(d["titulo"])}</span></span><span class="chev">›</span>', "dayrow"))
datas = {d["id"]: f'{ANO}-{d["data"][3:5]}-{d["data"][:2]}' for d in D["dias"]}
home = f'''
<div class="cover">
  <div class="kick gold">Guia de viagem</div>
  <div class="orn"></div>
  <h1 class="roma">Roma</h1>
  <div class="amore">con Amore</div>
  <div class="orn"></div>
  <div class="sub">{e(D["subtitulo"])}</div>
  <div class="grp">{e(D["grupo"])}</div>
</div>
<a id="hoje" class="btn gold big" href="#" hidden></a>
<div class="wrap">
  <div class="kick">Roma con Amore</div>
  <h2 class="h">Sumário</h2>
  <p class="muted small">Toque em um dia para abrir a programação.</p>
  <nav class="days">{"".join(rows)}</nav>
  <div class="btn3">{go("checklist", "Antes de ir", "btn")}{go("reservas", "Reservas", "btn gold")}{go("hospedagem", "Hospedagem", "btn line")}</div>
  <p id="instalar" class="tip" hidden></p>
</div>
<script>window.DATAS = {json.dumps(datas)};</script>'''
page("inicio", home, "Roma con Amore", "home")

def simple_head(kick, title, sub=None):
    s = f'<div class="kick">{e(kick)}</div><h2 class="h">{e(title)}</h2>'
    if sub: s += f'<p class="muted small">{e(sub)}</p>'
    return s + '<hr>'

# ------------------------------------------------------------- antes de partir
items = []
for n, it in enumerate(R["pendencias"]):
    key = "chk-" + hashlib.md5(it["texto"].encode()).hexdigest()[:10]
    txt = e(it["texto"])
    if it.get("ref") in L: txt += f' {go(it["ref"], "Ver ›", "more")}'
    items.append(f'<label class="chk"><input type="checkbox" data-k="{key}"><span>{txt}</span></label>')
page("checklist", '<div class="wrap">' + simple_head("Preparativos", "Antes de partir", D.get("aviso"))
     + '<p class="muted small">Marque o que já foi feito: fica salvo neste celular.</p>'
     + "".join(items) + "</div>", "Antes de partir")

# ------------------------------------------------------------- reservas
rs = []
for r in R["itens"]:
    inner = (f'<div class="rtop"><span class="rdate">{e(r["data"])}</span>{pill(r["status"])}</div>'
             f'<div class="rtt">{e(r["titulo"])}</div>'
             + (f'<div class="muted small">{e(r["detalhe"])}</div>' if r.get("detalhe") else ""))
    rs.append(go(r["ref"], inner + '<span class="chev">›</span>', "res") if r.get("ref") in L else f'<div class="res">{inner}</div>')
page("reservas", '<div class="wrap">' + simple_head("Reservas e ingressos", "Reservas e ingressos",
     "Toque em um item para ver os detalhes.") + "".join(rs) + "</div>", "Reservas")

# ------------------------------------------------------------- hospedagem
h = D["hospedagem"]
b = '<div class="wrap">' + simple_head("Onde ficamos", h["nome"])
for lab, k in (("Endereço", "endereco"), ("Chegada", "checkin"), ("Saída", "checkout")):
    b += f'<div class="kick muted">{lab}</div><p class="field">{e(h[k])}</p>'
b += '<div class="btn2">' + ext(gmaps(h["endereco"]), "Abrir no mapa", "btn")
if h.get("praca"): b += go("praca", "A praça", "btn line")
b += "</div>"
if h.get("chegada"): b += go("chegada", "Do aeroporto até a casa ›", "btn gold wide")
b += f'<div class="kick muted">O bairro</div><p class="lead">{e(h["obs"])}</p>'
if h.get("mercados"):
    mk = h["mercados"]
    b += f'<hr><div class="kick muted">Mercados por perto</div><p class="small">{e(mk["texto"])}</p>'
    b += ext(mk["mapa"], "Ver mercados no mapa", "btn wide")
    for lug in mk.get("lugares", []):
        b += ext(gmaps(lug["mapa"]), f'<div class="rtt">{e(lug["nome"])}</div><div class="muted small">{e(lug["endereco"])}</div>'
                 + (f'<div class="muted small">{e(lug["nota"])}</div>' if lug.get("nota") else "")
                 + '<span class="maptag">Mapa ›</span>', "res")
b += "</div>"
page("hospedagem", b, "Hospedagem")

if h.get("chegada"):
    ch = h["chegada"]
    b = f'<div class="wrap"><div class="kick">Onde ficamos · chegada</div><h2 class="h">{e(ch["titulo"])}</h2><p class="lead">{e(ch["resumo"])}</p><ol class="steps">'
    for tit, txt in ch["passos"]:
        b += f'<li><div class="rtt">{e(tit)}</div><p class="small">{e(txt)}</p></li>'
    b += '</ol><div class="btn2 wrapbtn">' + "".join(ext(u, e(lab), "btn line") for lab, u in ch["links"]) + "</div>"
    b += go("hospedagem", "‹ Hospedagem", "chip") + "</div>"
    page("chegada", b, "Chegada")

if h.get("praca"):
    pr = h["praca"]
    b = f'<div class="wrap"><div class="kick">Onde ficamos · a praça</div><h2 class="h">{e(pr["titulo"])}</h2>'
    if pr.get("foto"):
        b += f'<figure>{img(pr["foto"], "hero", pr["titulo"])}<figcaption>{e(pr.get("legenda"))}</figcaption></figure>'
    for titulo, its in pr["secoes"]:
        b += f'<div class="kick gold sec">{e(titulo)}</div><ul class="dots">' + "".join(f"<li>{e(x)}</li>" for x in its) + "</ul>"
    b += go("hospedagem", "‹ Hospedagem", "chip") + "</div>"
    page("praca", b, "A praça")

# ------------------------------------------------------------- dias
for i, d in enumerate(D["dias"]):
    mapas, letras, multi = route_plan(d)
    legs = leg_maps(d)
    b = (f'<header class="dayhead"><span class="big">{e(d["data"][:2])}</span>'
         f'<div class="kick lgold">Dia {i + 1} · {e(d["semana"])} · {e(d["data"])}</div>'
         f'<h2>{e(d["titulo"])}</h2><span class="bar"></span></header><div class="wrap">'
         f'<p class="lead">{e(d["intro"])}</p>')
    if mapas:
        b += f'<div class="kick muted">Pins na ordem da visita · {"1A" if multi else "A"} = apartamento</div>'
        if len(mapas) == 1: b += ext(mapas[0], "Mapa do percurso do dia", "btn wide")
        else: b += '<div class="btn2">' + "".join(ext(u, f"Mapa {k + 1} (pins {k + 1}A, {k + 1}B…)", "btn") for k, u in enumerate(mapas)) + "</div>"
    if d.get("pendencia"):
        b += f'<div class="alert"><div class="kick wine">Pendência</div><p>{e(d["pendencia"])}</p></div>'
    b += '<ol class="tl">'
    for k, it in enumerate(d["itens"]):
        isref = it.get("ref") in L
        alvo = it["ref"] if isref else it.get("link")
        mark = (f'<span class="pin">{e(letras[k])}</span>' if k in letras
                else f'<span class="dot {"ref" if it.get("ref") else e(it.get("tipo") or "")}"></span>')
        core = (f'<span class="hora{" g" if it.get("ref") else ""}">{e(it["hora"])}</span>{mark}'
                f'<span class="body"><span class="{"ttl" if it.get("ref") else "ttl2"}">{e(it["titulo"])}</span>'
                + (f'<span class="nota">{e(it["nota"])}</span>' if it.get("nota") else "") + "</span>")
        leg = ext(legs[k], "Mapa do trecho ›", "leg") if k in legs else ""
        if alvo:
            b += f'<li class="it">{go(alvo, core + "<span class=chev>›</span>", "row")}{leg}</li>'
        elif k in legs:
            b += f'<li class="it">{ext(legs[k], core + "<span class=legin>Mapa do trecho ›</span>", "row")}</li>'
        else:
            b += f'<li class="it"><div class="row">{core}</div></li>'
    b += "</ol>"
    prev = D["dias"][i - 1] if i else None
    nxt = D["dias"][i + 1] if i + 1 < len(D["dias"]) else None
    b += ('<nav class="pn">' + (go(prev["id"], "‹ " + e(prev["data"]), "chip") if prev else "<span></span>")
          + go("inicio", "Sumário", "chip") + (go(nxt["id"], e(nxt["data"]) + " ›", "chip") if nxt else "<span></span>") + "</nav></div>")
    page(d["id"], b, f'{d["data"]} · {d["titulo"]}', "day")

# ------------------------------------------------------------- locais
def gallery(p):
    fs = [f for f in p.get("fotos", []) if foto(f)]
    if not fs:
        return ext(gimg(p["nome"] + " Roma"), '<span>Ver fotos ›</span>', "nophoto")
    if len(fs) == 1:
        cap = f'<figcaption>{e(p["legenda_foto"])}</figcaption>' if p.get("legenda_foto") else ""
        return f'<figure>{img(fs[0], "hero", p["nome"])}{cap}</figure>'
    return ('<div class="gal">' + "".join(img(f, "", p["nome"]) for f in fs) + '</div>'
            f'<div class="galhint">{len(fs)} fotos · deslize para o lado ›</div>')

for key, p in L.items():
    dias_ref = ref_dias.get(key, [])
    kick = "Reserva" if p.get("tipo") == "restaurante" else ("Sugestão" if p.get("tipo") == "sugestao" else "Atração")
    if dias_ref: kick += " · " + " · ".join(d["data"] for d in dias_ref)
    wk = ext(p["wikipedia"], "Wikipédia ›", "wiki") if p.get("wikipedia") else ""
    b = f'<div class="wrap"><div class="kickrow"><div class="kick">{e(kick)}</div>{wk}</div><h2 class="h">{e(p["nome"])}</h2>{gallery(p)}'
    b += ('<div class="btn2">' + ext(gmaps(p.get("mapa") or p.get("endereco") or p["nome"] + " Roma"), "Como chegar", "btn")
          + ext(gimg(p["nome"] + " Roma"), "Mais fotos", "btn line") + "</div>")
    grupos = p.get("topicos") or ([{"botao": p.get("extras_botao", "História"), "secoes": p["extras"]}] if p.get("extras") else [])
    for gi, g in enumerate(grupos):
        b += go(f"{key}-extras-{gi}", e(g["botao"]) + " ›", "btn gold wide")
    if p.get("sobre"): b += f'<div class="band">História</div><div class="serif">{paras(p["sobre"])}</div>'
    if p.get("destaques"): b += f'<div class="band">Não perca</div><div class="serif ital">{paras(p["destaques"])}</div>'
    if p.get("alerta"): b += f'<div class="alert"><div class="kick wine">Atenção</div>{paras(p["alerta"])}</div>'
    for lab, k in (("Endereço", "endereco"), ("Horário", "horario"), ("Ingresso", "ingresso"), ("Dica", "dica")):
        if p.get(k): b += f'<div class="band">{lab}</div><div class="small">{paras(p[k])}</div>'
    for r in res_by_ref.get(key, []):
        b += (f'<div class="band">Reserva</div><div class="small"><p>{pill(r["status"])} {e(r["titulo"])}'
              + (f' — {e(r["detalhe"])}' if r.get("detalhe") else "") + "</p></div>")
    if p.get("links"):
        b += '<div class="kick muted sec">Opções</div>' + "".join(go(lk, e(L[lk]["nome"]), "btn line wide") for lk in p["links"] if lk in L)
    b += voltar_dia(dias_ref) + "</div>"
    page(key, b, p.get("nome_curto") or p["nome"])
    for gi, g in enumerate(grupos):
        b = (f'<div class="wrap"><div class="kick">{e(kick)} · {e(g["botao"].lower())}</div>'
             f'<h2 class="h">{e(g.get("titulo", p["nome"]))}</h2>')
        for sec in g["secoes"]:
            b += f'<div class="band">{e(sec["titulo"])}</div>'
            if sec.get("foto") and foto(sec["foto"]):
                b += f'<figure>{img(sec["foto"], "hero", sec["titulo"])}' + (f'<figcaption>{e(sec["legenda"])}</figcaption>' if sec.get("legenda") else "") + "</figure>"
            elif sec.get("buscar"):
                b += ext(gimg(sec["buscar"]), "<span>Ver fotos ›</span>", "nophoto small")
            for par_ in sec["texto"].split("\n"):
                if not par_.strip(): continue
                if par_.startswith("§"): b += f'<div class="kick gold sec">{e(par_[1:].strip())}</div>'
                else: b += f'<p class="serif">{e(par_)}</p>'
        b += go(key, "‹ Voltar a " + e(p.get("nome_curto") or p["nome"].split(" e ")[0]), "chip") + "</div>"
        page(f"{key}-extras-{gi}", b, g["botao"])

# ------------------------------------------------------------- ícones
def icon(size, path, pad=0.0):
    im = Image.new("RGB", (size, size), "#7A2E1F"); dr = ImageDraw.Draw(im)
    s = size; inset = int(s * (0.1 + pad))
    dr.rectangle([inset, inset, s - inset, s - inset], outline="#B8893B", width=max(2, s // 90))
    f1 = ImageFont.truetype(os.path.join(src, "fonts", "Lora-600.ttf"), int(s * (0.30 - pad * 0.4)))
    f2 = ImageFont.truetype(os.path.join(src, "fonts", "Lora-MediumItalic.ttf"), int(s * (0.13 - pad * 0.2)))
    dr.text((s / 2, s * 0.47), "Roma", font=f1, fill="#FFFDF9", anchor="ms")
    dr.text((s / 2, s * 0.66), "con Amore", font=f2, fill="#E8C987", anchor="ms")
    im.save(os.path.join(out, path))
icon(512, "icons/icon-512.png"); icon(192, "icons/icon-192.png"); icon(180, "icons/apple-touch-icon.png")
icon(512, "icons/maskable-512.png", pad=0.06)

# ------------------------------------------------------------- arquivos do app
here = os.path.dirname(os.path.abspath(__file__))
css = open(os.path.join(here, "app.css"), encoding="utf-8").read()
js = open(os.path.join(here, "app.js"), encoding="utf-8").read()
open(os.path.join(out, "app.css"), "w", encoding="utf-8").write(css)
open(os.path.join(out, "app.js"), "w", encoding="utf-8").write(js)

index = f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Roma con Amore</title>
<meta name="description" content="{e(D["titulo"])} · {e(D["subtitulo"])}">
<meta name="theme-color" content="#7A2E1F">
<meta name="color-scheme" content="light">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Roma">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="stylesheet" href="app.css">
</head>
<body>
<div class="topbar"><button id="voltar" aria-label="Voltar">‹</button><span id="titulo">Roma con Amore</span><a id="casa" href="#inicio" aria-label="Sumário">☰</a></div>
<main>
{"".join(PAGES)}
</main>
<script src="app.js"></script>
</body>
</html>'''
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index)

manifest = {"name": "Roma con Amore", "short_name": "Roma", "lang": "pt-BR", "start_url": "./", "scope": "./",
            "display": "standalone", "background_color": "#F7F1E6", "theme_color": "#7A2E1F",
            "icons": [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                      {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
                      {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
json.dump(manifest, open(os.path.join(out, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# service worker: guarda tudo para funcionar sem internet; a versão muda quando qualquer arquivo muda
files = []
for root, _, fs in os.walk(out):
    if ".git" in root: continue
    for f in fs:
        rel = os.path.relpath(os.path.join(root, f), out).replace(os.sep, "/")
        if rel not in ("sw.js", "CNAME") and not rel.startswith("."): files.append(rel)
files.sort()
hsh = hashlib.sha1()
for f in files: hsh.update(f.encode()); hsh.update(open(os.path.join(out, f), "rb").read())
ver = hsh.hexdigest()[:10]
sw = open(os.path.join(here, "sw.js"), encoding="utf-8").read()
sw = sw.replace("__VERSAO__", ver).replace("__ARQUIVOS__", json.dumps(["./"] + files, indent=0))
open(os.path.join(out, "sw.js"), "w", encoding="utf-8").write(sw)
open(os.path.join(out, ".nojekyll"), "w").write("")
tot = sum(os.path.getsize(os.path.join(out, f)) for f in files)
print(f"ok {out}: {len(PAGES)} telas, {len(files)} arquivos, {tot / 1e6:.1f} MB, versão {ver}")
