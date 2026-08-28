#!/usr/bin/env python3
"""
Generador autocontenido del sitio de l'AFA CEIP Alejandra Soler.

Llig NOMÉS `content/` (YAML) i `assets/` d'este mateix repositori — cap ruta
absoluta del Mac, cap dependència de `material/` ni de cap altra carpeta fora
del repo. Escriu el lloc a `dist/`.

Per què este disseny (ADR 002, docs/adr/002-editor-visual-pages-cms.md):
la junta (Mar/Laura) edita amb **Pages CMS** sobre estos fitxers YAML —
mai toquen HTML. Cada `git push` (fet pel propi CMS en guardar) dispara
`.github/workflows/build.yml`, que executa este script i publica `dist/`
a GitHub Pages amb el mètode oficial (upload-pages-artifact + deploy-pages).

Variable d'entorn PREVIEW=1 (usada pel repositori pilot de proves, mai pel
del AFA en producció):
  - afig <meta name="robots" content="noindex, nofollow"> (perquè Google no
    indexe la preview)
  - no escriu el fitxer CNAME (la preview no té domini propi)

Ús local:
    cd build && pip install -r requirements.txt
    python3 generar.py                  # build de producció
    PREVIEW=1 python3 generar.py        # build de preview (sense CNAME, amb noindex)

Fecha: 2026-08-27. No borrar (política del proyecto: scripts amb data,
mai s'esborren).
"""
import os
import re
import shutil
import unicodedata

import markdown
import yaml

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BUILD_DIR)
CONTENT = os.path.join(ROOT, "content")
ASSETS_SRC = os.path.join(ROOT, "assets")
DIST = os.path.join(ROOT, "dist")

PREVIEW = os.environ.get("PREVIEW") == "1"
DOMINI = "afaalejandrasoler.es"


# --------------------------------------------------------------------------
# Utilidades de contingut (YAML + passthrough HTML/markdown)
# --------------------------------------------------------------------------

def load_yaml(relpath):
    with open(os.path.join(CONTENT, relpath), encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_collection(subdir):
    """Carrega tots els .yml d'una carpeta (ignora els que comencen per _,
    p. ex. _comissions.yml, que és un fitxer de suport, no una fitxa)."""
    dirpath = os.path.join(CONTENT, subdir)
    items = []
    for fitxer in sorted(os.listdir(dirpath)):
        if fitxer.endswith(".yml") and not fitxer.startswith("_"):
            slug = fitxer[:-len(".yml")]
            data = load_yaml(os.path.join(subdir, fitxer))
            data["_slug"] = slug
            items.append(data)
    return items


def cos_html(text):
    """El contingut llarg (`cos`, `descripcio`, `nota`, `cos_valencia`...) es
    guarda en YAML com a HTML pla (paràgrafs, `<div>` amb classes pròpies del
    disseny — caixes, botons, requadres d'avís). markdown.markdown() amb
    l'extensió 'extra' deixa els blocs HTML EXACTAMENT igual (pass-through),
    i a més permet que la junta escriga en markdown senzill (negretes amb
    **, enllaços amb [text](url)...) en els camps que edite de nou.
    Verificat: 0 diferències contra el HTML original (ver docs/REGISTRO_TECNICO.md)."""
    if text is None:
        return ""
    return markdown.markdown(text.strip(), extensions=["extra"])


# --------------------------------------------------------------------------
# Rutes locals dels assets: qualsevol URL de la web anterior
# (ampaalejandrasoler.es/wp-content/uploads/...) es reescriu a la ruta local
# `assets/uploads/...` d'este repositori. Els enllaços externs (Google Drive,
# Google Forms, Aulazon...) es deixen tal qual.
# --------------------------------------------------------------------------

def local_asset_href(depth, url):
    """Reescriu a ruta relativa local si `url` és:
    - un fitxer de la web anterior (ampaalejandrasoler.es/wp-content/uploads/...),
      ja copiat a assets/uploads/ en la migració, o
    - una ruta pròpia del repo (p. ex. `assets/img/portades/x.jpg`, o
      `/assets/uploads/cms/x.pdf` — així és com Pages CMS escriu les rutes
      dels fitxers pujats des de l'editor, amb barra inicial).
    Si no és cap de les dos (Google Drive, Google Forms, Aulazon...), es
    deixa tal qual: és un enllaç extern."""
    if url is None:
        return None
    m = re.search(r"/wp-content/uploads/(.+)$", url)
    if m:
        return rel(depth, "assets/uploads/" + m.group(1))
    if url.startswith("assets/"):
        return rel(depth, url)
    if url.startswith("/assets/"):
        return rel(depth, url.lstrip("/"))
    return url


def rel(depth, target):
    return ("../" * depth) + target


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def initials(text):
    text = re.split(r"[/(]", text)[0].strip()
    words = re.sub(r"[^A-Za-zÀ-ÿ0-9 ]", " ", text).split()
    words = [w for w in words if w.lower() not in ("i", "de", "la", "el", "in", "the")]
    if not words:
        return "??"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()



# --------------------------------------------------------------------------
# Cursos / nivells (28-08-2026): cada fitxa porta `cursos` = llista de codis
# (I3/I4/I5 = Infantil 3/4/5 anys; P1..P6 = Primària), llegida del dossier
# de cada activitat. La landing els usa per al desplegable "Mostrar només".
# --------------------------------------------------------------------------
NIVELLS = [
    ("I3", "3 anys"), ("I4", "4 anys"), ("I5", "5 anys"),
    ("P1", "1r de Primària"), ("P2", "2n de Primària"), ("P3", "3r de Primària"),
    ("P4", "4t de Primària"), ("P5", "5é de Primària"), ("P6", "6é de Primària"),
]
INFANTIL = ["I3", "I4", "I5"]
PRIMARIA = ["P1", "P2", "P3", "P4", "P5", "P6"]
TOTS_ELS_CURSOS = INFANTIL + PRIMARIA
_ORDINALS = {"P1": "1r", "P2": "2n", "P3": "3r", "P4": "4t", "P5": "5é", "P6": "6é"}


def format_cursos(codes):
    """Text compacte per a la fitxa: '4 i 5 anys · 1r a 3r de Primària'.
    Buit si la fitxa no declara cursos (el dossier no els especifica)."""
    if not codes:
        return ""
    ordre = [c for c, _ in NIVELLS]
    codes = [c for c in ordre if c in codes]
    inf = [c for c in codes if c.startswith("I")]
    pri = [c for c in codes if c.startswith("P")]
    parts = []
    if inf:
        anys = [c[1] for c in inf]
        if len(anys) == 3:
            parts.append("Infantil (3, 4 i 5 anys)")
        elif len(anys) == 2:
            parts.append(f"{anys[0]} i {anys[1]} anys")
        else:
            parts.append(f"{anys[0]} anys")
    if pri:
        idx = [int(c[1]) for c in pri]
        consecutius = idx == list(range(idx[0], idx[-1] + 1))
        if len(idx) == 6:
            parts.append("tota la Primària (1r a 6é)")
        elif len(idx) == 1:
            parts.append(f"{_ORDINALS[pri[0]]} de Primària")
        elif consecutius:
            parts.append(f"{_ORDINALS[pri[0]]} a {_ORDINALS[pri[-1]]} de Primària")
        else:
            parts.append(", ".join(_ORDINALS[c] for c in pri[:-1]) + f" i {_ORDINALS[pri[-1]]} de Primària")
    return " · ".join(parts)


def ordre_edat(codes):
    """Índex del curs més menut de la fitxa (0 = 3 anys ... 8 = 6é); 99 si no
    declara cursos — així "Ordena per edat" les deixa al final."""
    ordre = [c for c, _ in NIVELLS]
    idx = [ordre.index(c) for c in (codes or []) if c in ordre]
    return min(idx) if idx else 99


def filtre_cursos_html():
    """Desplegable "Mostrar: <curs>" de la landing (orde sempre alfabètic, decisió Jorge 28-ago). Filtra
    i reordena les tarjetes en el navegador (sense recarregar) a partir dels
    atributs data-cursos / data-nom / data-ordre-edat de cada tarjeta. Les
    tarjetes amb data-cursos="*" (bloc municipal, o activitat que no declara
    cursos) es veuen sempre; el bloc municipal es queda sempre a l'últim."""
    opts = "\n".join(f'    <option value="{c}">{l}</option>' for c, l in NIVELLS)
    return f"""<div class="filtre-cursos">
  <label for="filtre-curs">Mostrar:</label>
  <select id="filtre-curs">
    <option value="">Totes les extraescolars</option>
{opts}
  </select>
  <span class="filtre-compte" id="filtre-compte" aria-live="polite"></span>
</div>
<script>
(function () {{
  var sel = document.getElementById('filtre-curs');
  var grid = document.querySelector('.grid-extraescolars');
  var compte = document.getElementById('filtre-compte');
  if (!sel || !grid) return;
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card-extra'));
  function aplica() {{
    var v = sel.value, n = 0;
    cards.forEach(function (c) {{
      var cursos = (c.getAttribute('data-cursos') || '').split(' ');
      var visible = !v || cursos.indexOf('*') !== -1 || cursos.indexOf(v) !== -1;
      c.hidden = !visible;
      if (visible) n++;
    }});
    compte.textContent = v ? n + ' extraescolar' + (n === 1 ? '' : 's') : '';
    var llista = cards.slice();
    llista.sort(function (a, b) {{
      var fa = a.hasAttribute('data-fixa-final') ? 1 : 0, fb = b.hasAttribute('data-fixa-final') ? 1 : 0;
      if (fa !== fb) return fa - fb;
      return a.getAttribute('data-nom') < b.getAttribute('data-nom') ? -1 : 1;
    }});
    llista.forEach(function (c) {{ grid.appendChild(c); }});
  }}
  sel.addEventListener('change', aplica);
}})();
</script>"""


def card_attrs(a, clau, fixa_final=False):
    """Atributs data-* d'una tarjeta de la landing (vore filtre_cursos_html)."""
    cursos = a.get("cursos") or []
    data_cursos = " ".join(cursos) if (cursos and not fixa_final) else "*"
    attrs = f' data-cursos="{data_cursos}" data-nom="{clau}" data-ordre-edat="{ordre_edat(cursos)}"'
    if fixa_final:
        attrs += ' data-fixa-final="1"'
    return attrs


def cursos_html(a):
    txt = format_cursos(a.get("cursos"))
    return f'<p class="fitxa-cursos"><strong>Cursos:</strong> {txt}</p>' if txt else ""


def empresa_html(a):
    e = a.get("empresa")
    return f'<p class="fitxa-empresa">Impartida per: <strong>{e}</strong></p>' if e else ""


def form_link_html(url, label):
    if url:
        return (f'<a class="recurs" href="{url}" target="_blank" rel="noreferrer noopener">'
                f'<span class="icona">📝</span> {label}</a>')
    return (f'<span class="recurs recurs-pendent"><span class="icona">📝</span> {label}: '
            f'pendent de publicar</span>')


# --------------------------------------------------------------------------
# Menú i plantilla comuna (idèntics als del clon original — no és contingut
# editable per la junta, viu ací com a codi).
# --------------------------------------------------------------------------
NAV = [
    {"label": "AFA", "children": [
        ("qui-som.html", "L'AFA"),
        ("fes-te-de-lafa.html", "Fes-te membre"),
        ("junta.html", "Junta AFA"),
        ("estatuts.html", "Estatuts AFA"),
    ]},
    {"label": "Extraescolars", "href": "extraescolars/index.html"},
    {"label": "Notícies", "children": [
        ("blog/index.html", "Blog"),
        ("galeria.html", "Galeria"),
    ]},
    {"label": "Projectes", "children": [
        ("mes-que-verd.html", "Més que verd"),
    ]},
    {"label": "Contacte", "href": "contacte.html"},
    {"label": "Fes-te membre", "href": "fes-te-de-lafa.html"},
    {"label": "WEB de l'escola", "href": "https://portal.edu.gva.es/46028430/", "extern": True},
]

FOOTER_LINKS_SECUNDARIS = [
    ("mes-que-verd.html", "Més que verd"),
    ("blog/index.html", "Blog"),
]


def build_nav_html(depth, active_href):
    parts = []
    for item in NAV:
        if "children" in item:
            child_hrefs = [h for h, _ in item["children"]]
            parent_actiu = " actiu" if active_href in child_hrefs else ""
            children_html = "\n        ".join(
                f'<li><a class="submenu-item{" actiu" if h == active_href else ""}" '
                f'href="{rel(depth, h)}">{label}</a></li>'
                for h, label in item["children"]
            )
            parts.append(f"""<div class="menu-item-parent">
        <button type="button" class="menu-item menu-toggle{parent_actiu}" aria-expanded="false" aria-haspopup="true" onclick="
          var s=this.nextElementSibling; var o=s.classList.toggle('obert'); this.setAttribute('aria-expanded', o);
        ">{item['label']} <span class="caret" aria-hidden="true"><svg width="11" height="7" viewBox="0 0 11 7" fill="none"><path d="M1 1l4.5 4.5L10 1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span></button>
        <ul class="submenu">
        {children_html}
        </ul>
      </div>""")
        else:
            href = item["href"]
            extern = item.get("extern")
            full_href = href if extern else rel(depth, href)
            is_actiu = " actiu" if href == active_href else ""
            target_attrs = ' target="_blank" rel="noreferrer noopener"' if extern else ""
            parts.append(f'<a class="menu-item{is_actiu}" href="{full_href}"{target_attrs}>{item["label"]}</a>')
    return "\n      ".join(parts)


def render_page(*, depth, active_href, title, meta_desc, body_html):
    css = rel(depth, "assets/css/style.css")
    logo = rel(depth, "assets/img/logo-afa.png")
    home = rel(depth, "index.html")
    nav_html = build_nav_html(depth, active_href)
    footer_extra = "\n            ".join(
        f'<li><a href="{rel(depth, href)}">{label}</a></li>' for href, label in FOOTER_LINKS_SECUNDARIS
    )
    head_extra = '<meta name="robots" content="noindex, nofollow">' if PREVIEW else ""

    return f"""<!DOCTYPE html>
<html lang="ca">
<head>{head_extra}
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · AFA CEIP Alejandra Soler</title>
<meta name="description" content="{meta_desc}">
<link rel="icon" href="{logo}">
<link rel="stylesheet" href="{css}">
</head>
<body>

<header class="site-header">
  <div class="wrap">
    <a class="marca" href="{home}">
      <img src="{logo}" alt="Logo AFA CEIP Alejandra Soler" width="44" height="74">
      <span>AFA CEIP Alejandra Soler<small>Russafa · València</small></span>
    </a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="menu-principal" onclick="
      var n=document.getElementById('menu-principal');
      var obert = n.classList.toggle('obert');
      this.setAttribute('aria-expanded', obert);
    ">☰ Menú</button>
    <nav class="menu-principal" id="menu-principal">
      {nav_html}
    </nav>
  </div>
</header>

<main>
{body_html}
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="cols">
      <div>
        <h4>AFA CEIP Alejandra Soler</h4>
        <ul>
          <li>Russafa, València</li>
          <li><a href="mailto:secretariaalejandrasoler@gmail.com">secretariaalejandrasoler@gmail.com</a></li>
          <li><a href="{rel(depth, 'contacte.html')}">Més contacte i xarxes</a></li>
        </ul>
      </div>
      <div>
        <h4>La web</h4>
        <ul>
          <li><a href="{rel(depth, 'qui-som.html')}">L'AFA</a></li>
          <li><a href="{rel(depth, 'extraescolars/index.html')}">Extraescolars</a></li>
          {footer_extra}
        </ul>
      </div>
      <div>
        <h4>Enllaços</h4>
        <ul>
          <li><a href="https://portal.edu.gva.es/46028430/" target="_blank" rel="noreferrer noopener">Web de l'escola</a></li>
          <li><a href="https://www.aulazon.es/categoria-producto/colegios/ceip-alejandra-soler/ampa-afa-ceip-alejandra-soler/" target="_blank" rel="noreferrer noopener">Pagament de quota (Aulazon)</a></li>
        </ul>
      </div>
    </div>
    <div class="avall">
      <span>© 2026 AFA CEIP Alejandra Soler. Domini i web propietat de l'AFA.</span>
    </div>
  </div>
</footer>

</body>
</html>
"""


def write(relpath, html):
    full = os.path.join(DIST, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)
    print("escrit:", relpath)


def asset_link(url, label, depth, icon="📄"):
    href = local_asset_href(depth, url)
    return f'<a class="recurs" href="{href}" target="_blank" rel="noreferrer noopener"><span class="icona">{icon}</span> {label}</a>'


def portada_img_html(depth, imatge_path, alt=""):
    """`imatge_path` ve del camp `imatge` del YAML (ruta relativa dins del
    repo, p. ex. assets/img/portades/judo.png), o None si no n'hi ha."""
    if not imatge_path:
        return None
    href = rel(depth, imatge_path)
    if imatge_path.endswith(".png"):
        return f'<img class="portada-logo" src="{href}" alt="Logotip de {alt}" loading="lazy">'
    return f'<img src="{href}" alt="{alt}" loading="lazy">'


# --------------------------------------------------------------------------
# Pàgina: INDEX (home) — no editable per la junta en v1 (fora d'abast, veure
# README.md "Per a la junta"). Contingut fix, igual que el clon original.
# --------------------------------------------------------------------------

def pagina_home():
    portada_href = local_asset_href(0, "https://ampaalejandrasoler.es/wp-content/uploads/2022/09/Portada_Web_22_23.png")
    body = f"""
<section class="hero">
  <div class="wrap">
    <span class="eyebrow">AFA CEIP Alejandra Soler · Russafa, València</span>
    <h1>La web de les famílies del cole</h1>
  </div>
</section>

<div class="wrap">

<section>
  <img class="imatge-doc" src="{portada_href}" alt="Portada AFA CEIP Alejandra Soler" loading="lazy">
</section>

<section>
  <div class="grid-accions">
    <a class="accio" href="extraescolars/index.html">
      <h3>Extraescolars 2026-27</h3>
      <p>Totes les activitats, els seus dossiers i l'enllaç d'inscripció.</p>
    </a>
    <a class="accio" href="blog/index.html">
      <h3>Blog</h3>
      <p>Notícies i avisos de l'AFA per a les famílies.</p>
    </a>
    <a class="accio" href="qui-som.html">
      <h3>Qui som</h3>
      <p>Una AFA multicultural al barri de Russafa.</p>
    </a>
    <a class="accio" href="contacte.html">
      <h3>Contacte</h3>
      <p>Escriu-nos o troba'ns a les xarxes.</p>
    </a>
  </div>
</section>

</div>
"""
    return render_page(
        depth=0, active_href="index.html",
        title="Inici",
        meta_desc="AFA del CEIP Alejandra Soler (Russafa, València): extraescolars, fes-te membre, junta i contacte.",
        body_html=body,
    )


# --------------------------------------------------------------------------
# Pàgines estàtiques (content/pagines/*.yml)
# --------------------------------------------------------------------------

def pagina_estatica(slug):
    d = load_yaml(f"pagines/{slug}.yml")
    body = f"""
<div class="page-hero"><div class="wrap"><h1>{d['titol']}</h1><p>{d['subtitol']}</p></div></div>
<div class="wrap">
<section>
{cos_html(d['cos'])}
</section>
</div>
"""
    return render_page(
        depth=0, active_href=f"{slug}.html",
        title=d.get("titol_pestanya", d["titol"]), meta_desc=d["meta_desc"], body_html=body,
    )


# --------------------------------------------------------------------------
# Junta (content/junta/*.yml)
# --------------------------------------------------------------------------

def pagina_junta():
    membres = load_collection("junta")
    membres.sort(key=lambda m: m.get("ordre", 999))
    comissions = load_yaml("junta/_comissions.yml")["comissions"]

    membres_html = []
    for m in membres:
        img = local_asset_href(0, m["imatge"])
        email_html = (f'<p class="fitxa-meta"><a href="mailto:{m["email"]}">{m["email"]}</a></p>'
                      if m.get("email") else "")
        membres_html.append(f"""<div class="wp-media-text">
  <img src="{img}" alt="" width="100" height="100" loading="lazy">
  <div><p>{m['carrec']}: <strong>{m['nom']}</strong></p>{email_html}</div>
</div>""")
    membres_html = "\n".join(membres_html)

    comissions_html = "\n".join(
        f'<li><strong>{c["nom"]}</strong> — Persona contacte: {c["contacte"]}</li>' for c in comissions
    )

    body = f"""
<div class="page-hero"><div class="wrap"><h1>Junta AFA</h1><p>Composició de la junta</p></div></div>
<div class="wrap">
<section>
<div class="junta-llista">
{membres_html}
</div>

<h2>Comissions AFA</h2>
<ul>
{comissions_html}
</ul>
<p><strong>Fem escola! Participa en les comissions!</strong></p>
<p>Si vols formar part i/o col·laborar en alguna de les comissions, escriu al correu
<a href="mailto:comissionsalejandrasoler@gmail.com">comissionsalejandrasoler@gmail.com</a> i et posarem en
contacte amb les persones responsables. Anima't! La teua ajuda és molt valuosa.</p>
</section>
</div>
"""
    return render_page(
        depth=0, active_href="junta.html",
        title="Junta AFA",
        meta_desc="Junta i comissions de l'AFA CEIP Alejandra Soler.",
        body_html=body,
    )


# --------------------------------------------------------------------------
# Blog (content/blog/*.yml)
# --------------------------------------------------------------------------

def pagina_blog_index(posts):
    cards = []
    for p in posts:
        cards.append(f"""<a class="post-card" href="{p['_slug']}.html">
  <time datetime="{p['data']}">{p['data_label']}</time>
  <h3>{p['titol']}</h3>
</a>""")
    cards_html = "\n".join(cards)
    body = f"""
<div class="page-hero"><div class="wrap"><h1>Blog</h1><p>Notícies i avisos de l'AFA</p></div></div>
<div class="wrap">
<section>
<div class="post-llista">
{cards_html}
</div>
</section>
</div>
"""
    return render_page(
        depth=1, active_href="blog/index.html",
        title="Blog",
        meta_desc="Blog de l'AFA CEIP Alejandra Soler: notícies i avisos per a les famílies.",
        body_html=body,
    )


def pagina_blog_post(p):
    imatge_html = ""
    if p.get("imatge"):
        img_href = local_asset_href(1, p["imatge"])
        imatge_html = f'<img class="imatge-doc" src="{img_href}" alt="{p["titol"]}" loading="lazy">'
    body = f"""
<div class="wrap">
<article>
<p class="fitxa-meta"><time datetime="{p['data']}">{p['data_label']}</time> · AFA CEIP Alejandra Soler</p>
<h1>{p['titol']}</h1>
<div class="post-cos">
{cos_html(p['cos_valencia'])}
<hr class="separador">
{cos_html(p['cos_castella'])}
</div>
{imatge_html}
<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="index.html">← Tot el blog</a>
</div>
</article>
</div>
"""
    return render_page(
        depth=1, active_href="blog/index.html",
        title=p["titol"],
        meta_desc=f"{p['titol']} — Blog de l'AFA CEIP Alejandra Soler.",
        body_html=body,
    )


# --------------------------------------------------------------------------
# Galeria — fora d'abast de l'editor v1 (contingut fix, igual que el clon).
# --------------------------------------------------------------------------
GALERIA_FOTOS = [
    ("2014/11/ampa100_0016__PLG6242.jpg", "Carrer del col·legi"),
    ("2014/11/ampa100_0009__PLG6116.jpg", "Pati, vista des de dalt"),
    ("2014/11/ampa100_0008__PLG6120.jpg", "Pati d'Infantil"),
    ("2014/11/ampa100_0005__PLG6092.jpg", "Passadís de l'escola"),
    ("2014/11/ampa100_0013__PLG6191.jpg", "Pati poliesportiu"),
    ("2014/11/ampa100_0001__PLG6109.jpg", "Aula"),
    ("2014/11/ampa100_0003__PLG6106.jpg", "Aula amb pissarra"),
    ("2014/03/banner-infantil1.jpg", "Edifici i pati d'Infantil"),
]


def pagina_galeria():
    fotos_grid = "\n".join(
        f'<a class="galeria-item" href="{local_asset_href(0, "https://ampaalejandrasoler.es/wp-content/uploads/" + url)}" '
        f'target="_blank" rel="noreferrer noopener">'
        f'<img src="{local_asset_href(0, "https://ampaalejandrasoler.es/wp-content/uploads/" + url)}" alt="{alt}" loading="lazy">'
        f'</a>'
        for url, alt in GALERIA_FOTOS
    )
    body = f"""
<div class="page-hero"><div class="wrap"><h1>Galeria</h1><p>Fotos de les instal·lacions del cole</p></div></div>
<div class="wrap">
<section>
<div class="grid-galeria">
{fotos_grid}
</div>
</section>
</div>
"""
    return render_page(
        depth=0, active_href="galeria.html",
        title="Galeria",
        meta_desc="Galeria de fotos de l'AFA CEIP Alejandra Soler.",
        body_html=body,
    )


# --------------------------------------------------------------------------
# Extraescolars (content/extraescolars/*.yml — inclou activitats-municipals)
# --------------------------------------------------------------------------

def _clau_alfabetica(nom):
    s = unicodedata.normalize("NFD", nom)
    return "".join(c for c in s if not unicodedata.combining(c) and c not in "'’").lower()


# Recursos fixos de la landing d'extraescolars (no són d'una activitat
# concreta, viuen com a codi — fora d'abast de l'editor v1).
HORARI_GENERAL = "https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls.-Horari-2526-4_page-0001.jpg"
PREUS_MUNICIPALS = "https://ampaalejandrasoler.es/wp-content/uploads/2025/09/Informacio-actv-municipals_-preus-i-cursos.pdf"
HORARIS_NIVELL = [
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls.-3-anys_page-0001.jpg", "3 anys"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0010.jpg", "4 anys"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0011.jpg", "5 anys"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0012.jpg", "1er Primària"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0013.jpg", "2n Primària"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0014.jpg", "3er Primària"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2025/09/Horari-i-espais-2025-2026xls.-4rt-prim_page-0001.jpg", "4t Primària"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2025/11/Horari-i-espais-2025-2026xls.-5e-prim_page-0001.jpg", "5é Primària"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2025/11/Horari-i-espais-2025-2026xls.-6e-prim_page-0001.jpg", "6é Primària"),
]


def pagina_extraescolars_landing(activitats, municipals):
    def _card(a, fixa_final=False):
        img_html = portada_img_html(1, a.get("imatge"), alt=a["nom"])
        # El bloc municipal mostra "FDM" (com el clon original), no les inicials
        inicials = "FDM" if fixa_final else initials(a["nom"])
        visual = img_html if img_html else f'<div class="placeholder-img {a["ph"]}">{inicials}</div>'
        return f"""<a class="card-extra" href="{a['_slug']}.html"{card_attrs(a, _clau_alfabetica(a['nom']), fixa_final=fixa_final)}>
  {visual}
  <div class="nom">{a['nom']}<small class="empresa">{a.get('empresa') or ''}</small></div>
</a>"""

    # Les activitats es mostren per orde alfabètic; "Activitats municipals
    # (FDM)" es queda sempre AL FINAL (no és una empresa, és un bloc apart),
    # clon fiel del comportament original. El desplegable de la landing pot
    # reordenar-les per edat al navegador (vore filtre_cursos_html).
    cards = [_card(a) for a in sorted(activitats, key=lambda a: _clau_alfabetica(a["nom"]))]
    cards.append(_card(municipals, fixa_final=True))
    grid = "\n".join(cards)

    horaris_grid = "\n".join(
        f'<a class="horari-item" href="{local_asset_href(1, url)}" target="_blank" rel="noreferrer noopener">'
        f'<img src="{local_asset_href(1, url)}" alt="Horari extraescolars {nivell}" loading="lazy">'
        f'<span>{nivell}</span></a>'
        for url, nivell in HORARIS_NIVELL
    )

    body = f"""
<div class="page-hero"><div class="wrap"><h1>Extraescolars 2026-2027</h1>
<p>Tria l'activitat per a vore el seu dossier i inscriure't</p></div></div>
<div class="wrap">
<section>
<p>Extraescolars per al curs 2026-27: activitats des d'Infantil a Primària perquè les nostres
criatures gaudeixen, practiquen esport, continuen desenvolupant les seues habilitats i
capacitats, i també perquè ajuden a conciliar a les famílies de l'escola.</p>
<p>Com sempre, tindrem extraescolars privades, impartides per empreses o professionals, i
extraescolars municipals, facilitades per la
<a href="https://www.fdmvalencia.es/es/" target="_blank" rel="noreferrer noopener">Fundació Esportiva Municipal</a>,
amb duració anual i preu reduït.</p>
<p>Les extraescolars es desenvolupen d'octubre a maig, tant en horari de menjador com de
vesprada de 16.30 h a 17.30 h o de 17.30 h a 18.30 h, i els divendres de 15 h a 16.30 h.</p>
<p>Per poder participar en les activitats extraescolars privades sense pagar matrícula, cal
fer-se soci/sòcia de l'AFA abans del 30 de setembre —
<a href="https://www.aulazon.es/categoria-producto/colegios/ceip-alejandra-soler/ampa-afa-ceip-alejandra-soler/" target="_blank" rel="noreferrer noopener">a través d'Aulazon</a>.</p>
<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="places-lliures.html">Vore places lliures del mes</a>
</div>
</section>

<section>
{filtre_cursos_html()}
<div class="grid-extraescolars">
{grid}
</div>
</section>

<section>
<h2>Horaris per curs</h2>
<p class="nota">Horaris del curs 2025-26. Els del curs 2026-27 es publicaran ací quan estiguen tancats.</p>
<div class="recursos">
""" + asset_link(HORARI_GENERAL, "Horari general", depth=1) + """
""" + asset_link(PREUS_MUNICIPALS, "Preus activitats municipals", depth=1) + """
</div>
<p class="nota">**Les activitats amb dos asteriscs, signifiquen que son activitats municipals, i
per tant, el preu és més reduït.</p>
<h3>Horari per nivell/curs</h3>
<div class="grid-horaris">
""" + horaris_grid + """
</div>
</section>

<section>
<h3>Baixes</h3>
<p class="nota">Qualsevol baixa en alguna activitat s'ha de comunicar directament al monitor/a o
empresa que la imparteix, amb còpia a
<a href="mailto:extraescolarsalejandrasoler@gmail.com">extraescolarsalejandrasoler@gmail.com</a>.
L'admissió es fa per ordre d'inscripció.</p>
</section>
</div>
"""
    return render_page(
        depth=1, active_href="extraescolars/index.html",
        title="Extraescolars",
        meta_desc="Extraescolars del CEIP Alejandra Soler curs 2026-27: activitats, dossiers i inscripció.",
        body_html=body,
    )


def pagina_activitat(a):
    resources = [asset_link(a["dossier"], a.get("dossier_label") or "Dossier", depth=1)]
    if a.get("dossier2"):
        resources.append(asset_link(a["dossier2"], a.get("dossier2_label") or "Dossier (alternatiu)", depth=1))
    resources.append(form_link_html(a.get("form"), "Formulari d'inscripció"))
    if a.get("form2"):
        resources.append(form_link_html(a["form2"], "Formulari alternatiu"))
    resources_html = "\n".join(resources)

    nota_html = f'<div class="avis">{cos_html(a["nota"])}</div>' if a.get("nota") else ""
    descripcio_html = f'<div class="descripcio">{cos_html(a["descripcio"])}</div>' if a.get("descripcio") else ""

    fitxa_img_html = portada_img_html(1, a.get("imatge"), alt=a["nom"])
    fitxa_visual = fitxa_img_html if fitxa_img_html else f'<div class="placeholder-img {a["ph"]}">{initials(a["nom"])}</div>'

    body = f"""
<div class="wrap">
<section>
<div class="fitxa-cap">
  {fitxa_visual}
  <div>
    <h1>{a['nom']}</h1>
    <p class="fitxa-meta">Extraescolar curs 2026-27 · CEIP Alejandra Soler</p>
    {empresa_html(a)}
    {cursos_html(a)}
  </div>
</div>

{descripcio_html}

<div class="recursos">
{resources_html}
</div>

{nota_html}

<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="index.html">← Totes les extraescolars</a>
</div>
</section>
</div>
"""
    return render_page(
        depth=1, active_href="extraescolars/index.html",
        title=a["nom"],
        meta_desc=f"{a['nom']} — extraescolar del CEIP Alejandra Soler, curs 2026-27. Dossier i inscripció.",
        body_html=body,
    )


def pagina_municipals(a):
    llista_html = "\n".join(f"<li>{x}</li>" for x in a["llista"])
    resources_html = "\n".join([
        asset_link(a["dossier"], "Dossier", depth=1),
        asset_link(a["inscripcio_pdf"], "Full d'inscripció (PDF)", depth=1),
        asset_link(a["bonificacio"], "Sol·licitud de bonificació", depth=1),
        asset_link(a["info_preus"], "Preus i cursos", depth=1),
    ])
    fitxa_img_html = portada_img_html(1, a.get("imatge"), alt=a["nom"])
    fitxa_visual = fitxa_img_html if fitxa_img_html else '<div class="placeholder-img ph-6">FDM</div>'

    body = f"""
<div class="wrap">
<section>
<div class="fitxa-cap">
  {fitxa_visual}
  <div>
    <h1>{a['nom']}</h1>
    <p class="fitxa-meta">Fundació Esportiva Municipal · convocatòria gener-maig</p>
  </div>
</div>

<p>Activitats facilitades per la
<a href="https://www.fdmvalencia.es/es/" target="_blank" rel="noreferrer noopener">Fundació Esportiva Municipal</a>,
amb duració anual i preu reduït. No tenen panell propi d'empresa: les gestiona la FDM/l'AFA.</p>

<ul>{llista_html}</ul>

<p>El pagament es fa en dos terminis, el primer a l'inici d'octubre i el segon a finals de
gener, excepte si eres una família beneficiaria de la beca del menjador, quan el preu encara
és més reduït i el pagament es fa en un únic termini.</p>

<h3>Com inscriure's</h3>
<p>Cal omplir un formulari d'inscripció per activitat i enviar-lo junt amb el justificant de
pagament a <a href="mailto:extraescolarsalejandrasoler@gmail.com">extraescolarsalejandrasoler@gmail.com</a>.
En cas de ser beneficiari/ària de la beca de menjador, es pot optar a una bonificació en la
quota (formulari de baix).</p>

<div class="recursos">
{resources_html}
</div>

<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="index.html">← Totes les extraescolars</a>
</div>
</section>
</div>
"""
    return render_page(
        depth=1, active_href="extraescolars/index.html",
        title=a["nom"],
        meta_desc="Activitats extraescolars municipals (FDM) del CEIP Alejandra Soler.",
        body_html=body,
    )


def pagina_places_lliures():
    d = load_yaml("places-lliures.yml")
    img_href = local_asset_href(1, d["imatge"])
    body = f"""
<div class="wrap">
<section>
<h1>Places lliures</h1>
<p class="fitxa-meta">Calendari mensual d'extraescolars amb places disponibles</p>

<p>Consulta la imatge per a conéixer quines extraescolars tenen places lliures i fes la
inscripció en l'enllaç del formulari de cada activitat.</p>
<p class="nota"><em>Consulta la imagen para saber qué extraescolares tienen plazas libres y haz
la inscripción en el enlace del formulario de cada actividad.</em></p>

<h2>Últim publicat — {d['mes_label']}</h2>
<p class="nota">Encara no s'ha publicat el calendari del curs 2026-27. Es mostra, a tall
d'exemple, l'últim calendari publicat del curs anterior.</p>
<a class="horari-item horari-item-gran" href="{img_href}" target="_blank" rel="noreferrer noopener">
  <img class="imatge-doc" src="{img_href}" alt="Calendari de places lliures — últim publicat, curs 2025-26" loading="lazy">
  <span>Fes clic per a ampliar la imatge</span>
</a>

<h3>Llegenda</h3>
<ul>
  <li><strong>(n)</strong> entre parèntesis = places lliures disponibles</li>
  <li>Sense parèntesi = places il·limitades</li>
  <li><span class="semaforo s-rojo">Sense places</span> quan no en queda cap</li>
  <li><span class="semaforo s-naranja">Últimes places</span> quan en queden poques</li>
</ul>

<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="index.html">← Totes les extraescolars</a>
</div>
</section>
</div>
"""
    return render_page(
        depth=1, active_href="extraescolars/index.html",
        title="Places lliures",
        meta_desc="Places lliures d'extraescolars del CEIP Alejandra Soler, calendari mensual.",
        body_html=body,
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    # Assets: es copien tal qual (ja viuen en el repo, no cal descarregar res).
    shutil.copytree(ASSETS_SRC, os.path.join(DIST, "assets"))

    write("index.html", pagina_home())
    for slug in ("qui-som", "fes-te-de-lafa", "contacte", "mes-que-verd", "estatuts"):
        write(f"{slug}.html", pagina_estatica(slug))
    write("junta.html", pagina_junta())
    write("galeria.html", pagina_galeria())

    posts = load_collection("blog")
    posts.sort(key=lambda p: p["data"], reverse=True)
    write("blog/index.html", pagina_blog_index(posts))
    for p in posts:
        write(f"blog/{p['_slug']}.html", pagina_blog_post(p))

    activitats_totes = load_collection("extraescolars")
    activitats_actives = [a for a in activitats_totes if a.get("activa", True)]
    municipals = next(a for a in activitats_actives if a.get("es_municipal"))
    activitats = [a for a in activitats_actives if not a.get("es_municipal")]

    write("extraescolars/index.html", pagina_extraescolars_landing(activitats, municipals))
    write("extraescolars/places-lliures.html", pagina_places_lliures())
    write(f"extraescolars/{municipals['_slug']}.html", pagina_municipals(municipals))
    for a in activitats:
        write(f"extraescolars/{a['_slug']}.html", pagina_activitat(a))

    if not PREVIEW:
        with open(os.path.join(DIST, "CNAME"), "w", encoding="utf-8") as f:
            f.write(DOMINI + "\n")

    with open(os.path.join(DIST, ".nojekyll"), "w"):
        pass

    print("Build completat a", DIST, "(PREVIEW)" if PREVIEW else "(producció)")


if __name__ == "__main__":
    main()
