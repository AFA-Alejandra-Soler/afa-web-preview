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

Bilingüe VA+ES (2026-09-02, dictamen arquitecto-web 28-ago): el lloc s'escriu
com DOS arbres — valencià a l'arrel (per defecte, idèntic al d'abans) i
castellà espill complet a `es/`. El contingut de cada YAML pot portar un
camp bessó `<camp>_es`; si la junta el deixa buit, `txt()` recorre al
valencià — mai es publica una pàgina a mitges. Tots els textos fixos de la
interfície (menú, peu, botons, etiquetes) viuen al diccionari `T` i s'obtenen
amb `t(lang, clau)`. Vore `docs/REGISTRO_TECNICO.md` (entrada 2026-09-02).

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

# Registre de pàgines indexables (04-09-2026, SEO): render_page() hi afig
# cada pàgina que escriu de veres i que NO porta noindex (ni és build
# PREVIEW) — mai una llista de rutes inventada a banda. generar_sitemap()
# el llig tal qual al final del build. Vore render_page() i generar_sitemap().
SITEMAP_ENTRIES = []

# Nivells extra que cada arbre suma per a arribar a `assets/` (que NOMÉS
# existix en l'arrel de `dist/`, mai dins de `dist/es/`) — vore rel_assets().
ROOT_OFFSET = {"va": 0, "es": 1}


# --------------------------------------------------------------------------
# Diccionari d'interfície (menú, peu, botons, etiquetes...) — TOT el text fix
# de la web viu ací, mai despatxat directament en un f-string. `t(lang, clau)`
# el llig; `txt(d, camp, lang)` fa el mateix per a un camp de YAML amb
# fallback a valencià si `<camp>_es` no existix o està buit.
# --------------------------------------------------------------------------
T = {
    "va": {
        "menu_toggle": "☰ Menú",
        "marca_subtitle": "Russafa · València",
        "logo_alt": "Logo AFA CEIP Alejandra Soler",
        "lang_val": "VAL",
        "lang_cast": "CAST",

        "nav_afa": "AFA",
        "nav_lafa": "L'AFA",
        "nav_fes_membre": "Fes-te membre",
        "nav_junta": "Junta AFA",
        "nav_estatuts": "Estatuts AFA",
        "nav_extraescolars": "Extraescolars",
        "nav_conciliacio": "Conciliació",
        "nav_noticies": "Notícies",
        "nav_blog": "Blog",
        "nav_galeria": "Galeria",
        "nav_projectes": "Projectes",
        "nav_mes_que_verd": "Més que verd",
        "nav_contacte": "Contacte",
        "nav_web_escola": "WEB de l'escola",

        "footer_afa_title": "AFA CEIP Alejandra Soler",
        "footer_russafa": "Russafa, València",
        "footer_mes_contacte": "Més contacte i xarxes",
        "footer_web_title": "La web",
        "footer_enllacos_title": "Enllaços",
        "footer_web_escola": "Web de l'escola",
        "footer_pagament": "Pagament de quota (Aulazon)",
        "footer_copyright": "© 2026 AFA CEIP Alejandra Soler. Domini i web propietat de l'AFA.",

        "home_title": "Inici",
        "home_meta_desc": "AFA del CEIP Alejandra Soler (Russafa, València): extraescolars, fes-te membre, junta i contacte.",
        "home_eyebrow": "AFA CEIP Alejandra Soler · Russafa, València",
        "home_h1": "La web de les famílies del cole",
        "home_portada_alt": "Portada AFA CEIP Alejandra Soler",
        "home_card1_title": "Extraescolars 2026-27",
        "home_card1_desc": "Totes les activitats, els seus dossiers i l'enllaç d'inscripció.",
        "home_card2_title": "Blog",
        "home_card2_desc": "Notícies i avisos de l'AFA per a les famílies.",
        "home_card3_title": "Qui som",
        "home_card3_desc": "Una AFA multicultural al barri de Russafa.",
        "home_card4_title": "Contacte",
        "home_card4_desc": "Escriu-nos o troba'ns a les xarxes.",

        "junta_h1": "Junta AFA",
        "junta_subtitle": "Composició de la junta",
        "junta_comissions_h2": "Comissions AFA",
        "junta_contacte_prefix": "Persona contacte: ",
        "junta_participa_h": "Fem escola! Participa en les comissions!",
        "junta_participa_p": ("Si vols formar part i/o col·laborar en alguna de les comissions, escriu al correu "
                               '<a href="mailto:comissionsalejandrasoler@gmail.com">comissionsalejandrasoler@gmail.com</a> '
                               "i et posarem en contacte amb les persones responsables. Anima't! La teua ajuda és molt valuosa."),
        "junta_meta_desc": "Junta i comissions de l'AFA CEIP Alejandra Soler.",

        "blog_h1": "Blog",
        "blog_subtitle": "Notícies i avisos de l'AFA",
        "blog_meta_desc": "Blog de l'AFA CEIP Alejandra Soler: notícies i avisos per a les famílies.",
        "blog_back": "← Tot el blog",
        "blog_post_meta_desc_suffix": " — Blog de l'AFA CEIP Alejandra Soler.",

        "galeria_h1": "Galeria",
        "galeria_subtitle": "Fotos de les instal·lacions del cole",
        "galeria_meta_desc": "Galeria de fotos de l'AFA CEIP Alejandra Soler.",

        "filtre_label": "Filtrar per curs:",
        "filtre_totes": "Totes les extraescolars",
        "filtre_extraescolar_singular": "extraescolar",
        "filtre_extraescolars_plural": "extraescolars",

        "fc_infantil_3": "Infantil (3, 4 i 5 anys)",
        "fc_anys": "anys",
        "fc_i": " i ",
        "fc_a": " a ",
        "fc_tota_primaria": "tota la Primària (1r a 6é)",
        "fc_de_primaria": "de Primària",

        "cursos_label": "Cursos:",
        "empresa_label": "Impartida per:",
        "pendent": "pendent de publicar",
        "pagina_en_preparacio": "Aquesta pàgina està en preparació. Prompte estarà disponible.",

        "extra_h1": "Extraescolars 2026-2027",
        "extra_subtitle": "Tria l'activitat per a vore el seu dossier i inscriure't",
        "extra_intro1": ("Extraescolars per al curs 2026-27: activitats des d'Infantil a Primària perquè les "
                          "nostres criatures gaudeixen, practiquen esport, continuen desenvolupant les seues "
                          "habilitats i capacitats, i també perquè ajuden a conciliar a les famílies de l'escola."),
        "extra_intro2": ("Com sempre, tindrem extraescolars privades, impartides per empreses o professionals, i "
                          'extraescolars municipals, facilitades per la <a href="https://www.fdmvalencia.es/es/" '
                          'target="_blank" rel="noreferrer noopener">Fundació Esportiva Municipal</a>, amb duració '
                          "anual i preu reduït."),
        "extra_intro3": ("Les extraescolars es desenvolupen d'octubre a maig, tant en horari de menjador com de "
                          "vesprada de 16.30 h a 17.30 h o de 17.30 h a 18.30 h, i els divendres de 15 h a 16.30 h."),
        "extra_intro4": ("Per poder participar en les activitats extraescolars privades sense pagar matrícula, cal "
                          'fer-se soci/sòcia de l\'AFA abans del 30 de setembre — <a href="https://www.aulazon.es/'
                          'categoria-producto/colegios/ceip-alejandra-soler/ampa-afa-ceip-alejandra-soler/" '
                          'target="_blank" rel="noreferrer noopener">a través d\'Aulazon</a>.'),
        "extra_btn_places": "Vore places lliures del mes",
        "extra_horaris_h2": "Horaris per curs",
        "extra_horaris_nota": "Horaris del curs 2025-26. Els del curs 2026-27 es publicaran ací quan estiguen tancats.",
        "extra_horari_general_label": "Horari general",
        "extra_horaris_municipals_label": "Horaris activitats municipals",
        "extra_asteriscs_nota": ("**Les activitats amb dos asteriscs, signifiquen que son activitats municipals, i "
                                  "per tant, el preu és més reduït."),
        "extra_horari_nivell_h3": "Horari per nivell/curs",
        "horari_alt_prefix": "Horari extraescolars",
        "extra_baixes_h3": "Baixes",
        "extra_baixes_p": ("Qualsevol baixa en alguna activitat s'ha de comunicar directament al monitor/a o "
                            'empresa que la imparteix, amb còpia a <a href="mailto:extraescolarsalejandrasoler@'
                            'gmail.com">extraescolarsalejandrasoler@gmail.com</a>. L\'admissió es fa per ordre '
                            "d'inscripció."),
        "extra_meta_desc": "Extraescolars del CEIP Alejandra Soler curs 2026-27: activitats, dossiers i inscripció.",

        "activitat_dossier_label": "Dossier",
        "activitat_dossier2_label": "Dossier (alternatiu)",
        "activitat_inscripcio_pdf_label": "Full d'inscripció (PDF)",
        "activitat_bonificacio_label": "Sol·licitud de bonificació",
        "activitat_info_preus_label": "Preus i cursos",
        "activitat_form_label": "Formulari d'inscripció",
        "activitat_form2_label": "Formulari alternatiu",
        "activitat_meta_line": "Extraescolar curs 2026-27 · CEIP Alejandra Soler",
        "activitat_back": "← Totes les extraescolars",
        "activitat_meta_desc_suffix": " — extraescolar del CEIP Alejandra Soler, curs 2026-27. Dossier i inscripció.",
        "portada_logo_alt_prefix": "Logotip de",

        "places_h1": "Places lliures",
        "places_subtitle": "Calendari mensual d'extraescolars amb places disponibles",
        "places_intro": ("Consulta la imatge per a conéixer quines extraescolars tenen places lliures i fes la "
                          "inscripció en l'enllaç del formulari de cada activitat."),
        "places_ultim_h2_prefix": "Últim publicat — ",
        "places_nota": ("Encara no s'ha publicat el calendari del curs 2026-27. Es mostra, a tall d'exemple, "
                         "l'últim calendari publicat del curs anterior."),
        "places_alt": "Calendari de places lliures — últim publicat, curs 2025-26",
        "places_click_ampliar": "Fes clic per a ampliar la imatge",
        "places_llegenda_h3": "Llegenda",
        "places_li1": "<strong>(n)</strong> entre parèntesis = places lliures disponibles",
        "places_li2": "Sense parèntesi = places il·limitades",
        "places_li3": '<span class="semaforo s-rojo">Sense places</span> quan no en queda cap',
        "places_li4": '<span class="semaforo s-naranja">Últimes places</span> quan en queden poques',
        "places_meta_desc": "Places lliures d'extraescolars del CEIP Alejandra Soler, calendari mensual.",
    },
    "es": {
        "menu_toggle": "☰ Menú",
        "marca_subtitle": "Russafa · Valencia",
        "logo_alt": "Logo AFA CEIP Alejandra Soler",
        "lang_val": "VAL",
        "lang_cast": "CAST",

        "nav_afa": "AFA",
        "nav_lafa": "La AFA",
        "nav_fes_membre": "Hazte socio/a",
        "nav_junta": "Junta AFA",
        "nav_estatuts": "Estatutos AFA",
        "nav_extraescolars": "Extraescolares",
        "nav_conciliacio": "Conciliación",
        "nav_noticies": "Noticias",
        "nav_blog": "Blog",
        "nav_galeria": "Galería",
        "nav_projectes": "Proyectos",
        "nav_mes_que_verd": "Más que verde",
        "nav_contacte": "Contacto",
        "nav_web_escola": "WEB del cole",

        "footer_afa_title": "AFA CEIP Alejandra Soler",
        "footer_russafa": "Russafa, Valencia",
        "footer_mes_contacte": "Más contacto y redes",
        "footer_web_title": "La web",
        "footer_enllacos_title": "Enlaces",
        "footer_web_escola": "Web del cole",
        "footer_pagament": "Pago de cuota (Aulazon)",
        "footer_copyright": "© 2026 AFA CEIP Alejandra Soler. Dominio y web propiedad del AFA.",

        "home_title": "Inicio",
        "home_meta_desc": "AFA del CEIP Alejandra Soler (Russafa, Valencia): extraescolares, hazte socio/a, junta y contacto.",
        "home_eyebrow": "AFA CEIP Alejandra Soler · Russafa, Valencia",
        "home_h1": "La web de las familias del cole",
        "home_portada_alt": "Portada AFA CEIP Alejandra Soler",
        "home_card1_title": "Extraescolares 2026-27",
        "home_card1_desc": "Todas las actividades, sus dosieres y el enlace de inscripción.",
        "home_card2_title": "Blog",
        "home_card2_desc": "Noticias y avisos del AFA para las familias.",
        "home_card3_title": "Quiénes somos",
        "home_card3_desc": "Un AFA multicultural en el barrio de Russafa.",
        "home_card4_title": "Contacto",
        "home_card4_desc": "Escríbenos o encuéntranos en las redes.",

        "junta_h1": "Junta AFA",
        "junta_subtitle": "Composición de la junta",
        "junta_comissions_h2": "Comisiones AFA",
        "junta_contacte_prefix": "Persona de contacto: ",
        "junta_participa_h": "¡Hagamos escuela! ¡Participa en las comisiones!",
        "junta_participa_p": ("Si quieres formar parte y/o colaborar en alguna de las comisiones, escribe al correo "
                               '<a href="mailto:comissionsalejandrasoler@gmail.com">comissionsalejandrasoler@gmail.com</a> '
                               "y te pondremos en contacto con las personas responsables. ¡Anímate! Tu ayuda es muy valiosa."),
        "junta_meta_desc": "Junta y comisiones del AFA CEIP Alejandra Soler.",

        "blog_h1": "Blog",
        "blog_subtitle": "Noticias y avisos del AFA",
        "blog_meta_desc": "Blog del AFA CEIP Alejandra Soler: noticias y avisos para las familias.",
        "blog_back": "← Todo el blog",
        "blog_post_meta_desc_suffix": " — Blog del AFA CEIP Alejandra Soler.",

        "galeria_h1": "Galería",
        "galeria_subtitle": "Fotos de las instalaciones del cole",
        "galeria_meta_desc": "Galería de fotos del AFA CEIP Alejandra Soler.",

        "filtre_label": "Filtrar por curso:",
        "filtre_totes": "Todas las extraescolares",
        "filtre_extraescolar_singular": "extraescolar",
        "filtre_extraescolars_plural": "extraescolares",

        "fc_infantil_3": "Infantil (3, 4 y 5 años)",
        "fc_anys": "años",
        "fc_i": " y ",
        "fc_a": " a ",
        "fc_tota_primaria": "toda la Primaria (1º a 6º)",
        "fc_de_primaria": "de Primaria",

        "cursos_label": "Cursos:",
        "empresa_label": "Impartida por:",
        "pendent": "pendiente de publicar",
        "pagina_en_preparacio": "Esta página está en preparación. Pronto estará disponible.",

        "extra_h1": "Extraescolares 2026-2027",
        "extra_subtitle": "Elige la actividad para ver su dosier e inscribirte",
        "extra_intro1": ("Extraescolares para el curso 2026-27: actividades desde Infantil hasta Primaria para "
                          "que nuestros niños y niñas disfruten, practiquen deporte, sigan desarrollando sus "
                          "habilidades y capacidades, y también para ayudar a conciliar a las familias del cole."),
        "extra_intro2": ("Como siempre, tendremos extraescolares privadas, impartidas por empresas o "
                          'profesionales, y extraescolares municipales, facilitadas por la <a href="https://www.'
                          'fdmvalencia.es/es/" target="_blank" rel="noreferrer noopener">Fundación Deportiva '
                          'Municipal</a>, con duración anual y precio reducido.'),
        "extra_intro3": ("Las extraescolares se desarrollan de octubre a mayo, tanto en horario de comedor como "
                          "de tarde de 16.30 h a 17.30 h o de 17.30 h a 18.30 h, y los viernes de 15 h a 16.30 h."),
        "extra_intro4": ("Para poder participar en las actividades extraescolares privadas sin pagar matrícula, "
                          'hay que hacerse socio/a del AFA antes del 30 de septiembre — <a href="https://www.'
                          'aulazon.es/categoria-producto/colegios/ceip-alejandra-soler/ampa-afa-ceip-alejandra-'
                          'soler/" target="_blank" rel="noreferrer noopener">a través de Aulazon</a>.'),
        "extra_btn_places": "Ver plazas libres del mes",
        "extra_horaris_h2": "Horarios por curso",
        "extra_horaris_nota": "Horarios del curso 2025-26. Los del curso 2026-27 se publicarán aquí cuando estén cerrados.",
        "extra_horari_general_label": "Horario general",
        "extra_horaris_municipals_label": "Horarios actividades municipales",
        "extra_asteriscs_nota": ("**Las actividades con dos asteriscos significan que son actividades "
                                  "municipales, y por tanto, el precio es más reducido."),
        "extra_horari_nivell_h3": "Horario por nivel/curso",
        "horari_alt_prefix": "Horario extraescolares",
        "extra_baixes_h3": "Bajas",
        "extra_baixes_p": ("Cualquier baja en alguna actividad se debe comunicar directamente al monitor/a o "
                            'empresa que la imparte, con copia a <a href="mailto:extraescolarsalejandrasoler@'
                            'gmail.com">extraescolarsalejandrasoler@gmail.com</a>. La admisión se realiza por '
                            "orden de inscripción."),
        "extra_meta_desc": "Extraescolares del CEIP Alejandra Soler curso 2026-27: actividades, dosieres e inscripción.",

        "activitat_dossier_label": "Dosier",
        "activitat_dossier2_label": "Dosier (alternativo)",
        "activitat_inscripcio_pdf_label": "Hoja de inscripción (PDF)",
        "activitat_bonificacio_label": "Solicitud de bonificación",
        "activitat_info_preus_label": "Precios y cursos",
        "activitat_form_label": "Formulario de inscripción",
        "activitat_form2_label": "Formulario alternativo",
        "activitat_meta_line": "Extraescolar curso 2026-27 · CEIP Alejandra Soler",
        "activitat_back": "← Todas las extraescolares",
        "activitat_meta_desc_suffix": " — extraescolar del CEIP Alejandra Soler, curso 2026-27. Dosier e inscripción.",
        "portada_logo_alt_prefix": "Logotipo de",

        "places_h1": "Plazas libres",
        "places_subtitle": "Calendario mensual de extraescolares con plazas disponibles",
        "places_intro": ("Consulta la imagen para saber qué extraescolares tienen plazas libres y haz la "
                          "inscripción en el enlace del formulario de cada actividad."),
        "places_ultim_h2_prefix": "Último publicado — ",
        "places_nota": ("Todavía no se ha publicado el calendario del curso 2026-27. Se muestra, a modo de "
                         "ejemplo, el último calendario publicado del curso anterior."),
        "places_alt": "Calendario de plazas libres — último publicado, curso 2025-26",
        "places_click_ampliar": "Haz clic para ampliar la imagen",
        "places_llegenda_h3": "Leyenda",
        "places_li1": "<strong>(n)</strong> entre paréntesis = plazas libres disponibles",
        "places_li2": "Sin paréntesis = plazas ilimitadas",
        "places_li3": '<span class="semaforo s-rojo">Sin plazas</span> cuando no queda ninguna',
        "places_li4": '<span class="semaforo s-naranja">Últimas plazas</span> cuando quedan pocas',
        "places_meta_desc": "Plazas libres de extraescolares del CEIP Alejandra Soler, calendario mensual.",
    },
}


def t(lang, key):
    """Text fix d'interfície (menú, peu, botons, etiquetes...) segons l'idioma."""
    return T[lang][key]


def txt(d, campo, lang):
    """Lectura d'un camp de text del YAML amb fallback a valencià: per a
    lang='es' torna `d.get(campo + '_es')` o, si és buit/no existix,
    `d.get(campo)`; per a 'va' torna directament `d.get(campo)`. Aplicar-la
    SEMPRE que es llija un camp de text d'una fitxa (nom, descripcio, nota,
    titol, subtitol, meta_desc, cos, carrec, mes_label, dossier_label...)."""
    if lang == "es":
        return d.get(campo + "_es") or d.get(campo)
    return d.get(campo)


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


_COS_ASSET_RE = re.compile(r'((?:href|src)=")(?:\.\./)*assets/')

# Post-procés final de render_page() (04-09-2026): reescriu qualsevol
# "/assets/..." absolut (deixat per cos_html() o pegat directament per la
# junta des de Pages CMS) a la ruta relativa correcta de CADA pàgina — vore
# el comentari a render_page(), just abans del return.
_ASSET_ABS_RE = re.compile(r'(href|src)="/assets/')


def cos_html(text):
    """El contingut llarg (`cos`, `descripcio`, `nota`, `cos_valencia`...) es
    guarda en YAML com a HTML pla (paràgrafs, `<div>` amb classes pròpies del
    disseny — caixes, botons, requadres d'avís). markdown.markdown() amb
    l'extensió 'extra' deixa els blocs HTML EXACTAMENT igual (pass-through),
    i a més permet que la junta escriga en markdown senzill (negretes amb
    **, enllaços amb [text](url)...) en els camps que edite de nou.
    Verificat: 0 diferències contra el HTML original (ver docs/REGISTRO_TECNICO.md).

    Alguns camps porten enllaços a `assets/uploads/...` escrits a mà amb una
    profunditat fixa ("assets/..." o "../assets/...", assumint sempre l'arbre
    únic d'abans del bilingüe). Amb l'arbre /es/ eixa profunditat ja no és
    fixa (02-09-2026), així que ho normalitzem sempre a ruta absoluta des de
    l'arrel del domini ("/assets/...") — `assets/` NOMÉS existix a l'arrel de
    `dist/`, mai duplicat dins de `dist/es/`, i una ruta absoluta funciona
    igual siga quina siga la profunditat real de la pàgina."""
    if text is None:
        return ""
    html = markdown.markdown(text.strip(), extensions=["extra"])
    return _COS_ASSET_RE.sub(r"\1/assets/", html)


# --------------------------------------------------------------------------
# Rutes locals dels assets: qualsevol URL de la web anterior
# (ampaalejandrasoler.es/wp-content/uploads/...) es reescriu a la ruta local
# `assets/uploads/...` d'este repositori. Els enllaços externs (Google Drive,
# Google Forms, Aulazon...) es deixen tal qual.
#
# `depth` en estes funcions és SEMPRE la "profunditat d'assets": nivells que
# cal pujar amb "../" per a arribar a `assets/`, que NOMÉS existix en l'arrel
# de `dist/` (mai dins de `dist/es/`). Cada pagina_X() la calcula com
# `depth_local + ROOT_OFFSET[lang]` — vore render_page() i alt_href().
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


def alt_href(lang, depth, page_path):
    """Ruta relativa des d'esta pàgina a la seua bessona en l'altre idioma
    (mateix `page_path`, l'arbre espill complet). `depth` és la profunditat
    LOCAL de la pàgina dins del seu propi arbre (0 = arrel, 1 = blog/,
    extraescolars/...), la mateixa que active_href fa servir per a la
    navegació interna — NO la "profunditat d'assets"."""
    if lang == "va":
        return rel(depth, "es/" + page_path)
    return rel(depth + 1, page_path)


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def initials(text):
    text = re.split(r"[/(]", text)[0].strip()
    words = re.sub(r"[^A-Za-zÀ-ÿ0-9 ]", " ", text).split()
    words = [w for w in words if w.lower() not in ("i", "de", "la", "el", "in", "the", "y")]
    if not words:
        return "??"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


# --------------------------------------------------------------------------
# Cursos / nivells (28-08-2026, bilingüe 02-09-2026): cada fitxa porta
# `cursos` = llista de codis (I3/I4/I5 = Infantil 3/4/5 anys; P1..P6 =
# Primària), llegida del dossier de cada activitat. La landing els usa per al
# desplegable "Mostrar només". Cada nivell porta etiqueta va + es.
# --------------------------------------------------------------------------
NIVELLS = [
    ("I3", "3 anys", "3 años"), ("I4", "4 anys", "4 años"), ("I5", "5 anys", "5 años"),
    ("P1", "1r de Primària", "1º de Primaria"), ("P2", "2n de Primària", "2º de Primaria"),
    ("P3", "3r de Primària", "3º de Primaria"), ("P4", "4t de Primària", "4º de Primaria"),
    ("P5", "5é de Primària", "5º de Primaria"), ("P6", "6é de Primària", "6º de Primaria"),
]
INFANTIL = ["I3", "I4", "I5"]
PRIMARIA = ["P1", "P2", "P3", "P4", "P5", "P6"]
TOTS_ELS_CURSOS = INFANTIL + PRIMARIA
_ORDINALS = {
    "va": {"P1": "1r", "P2": "2n", "P3": "3r", "P4": "4t", "P5": "5é", "P6": "6é"},
    "es": {"P1": "1º", "P2": "2º", "P3": "3º", "P4": "4º", "P5": "5º", "P6": "6º"},
}


def nivell_label(codi, lang):
    for c, va, es in NIVELLS:
        if c == codi:
            return va if lang == "va" else es
    return codi


def format_cursos(codes, lang):
    """Text compacte per a la fitxa: '4 i 5 anys · 1r a 3r de Primària' (va) /
    '4 y 5 años · 1º a 3º de Primaria' (es). Buit si la fitxa no declara
    cursos (el dossier no els especifica)."""
    if not codes:
        return ""
    ordre = [c for c, _, _ in NIVELLS]
    codes = [c for c in ordre if c in codes]
    inf = [c for c in codes if c.startswith("I")]
    pri = [c for c in codes if c.startswith("P")]
    ordinals = _ORDINALS[lang]
    anys_word = t(lang, "fc_anys")
    de_primaria = t(lang, "fc_de_primaria")
    parts = []
    if inf:
        anys = [c[1] for c in inf]
        if len(anys) == 3:
            parts.append(t(lang, "fc_infantil_3"))
        elif len(anys) == 2:
            parts.append(f"{anys[0]}{t(lang, 'fc_i')}{anys[1]} {anys_word}")
        else:
            parts.append(f"{anys[0]} {anys_word}")
    if pri:
        idx = [int(c[1]) for c in pri]
        consecutius = idx == list(range(idx[0], idx[-1] + 1))
        if len(idx) == 6:
            parts.append(t(lang, "fc_tota_primaria"))
        elif len(idx) == 1:
            parts.append(f"{ordinals[pri[0]]} {de_primaria}")
        elif consecutius:
            parts.append(f"{ordinals[pri[0]]}{t(lang, 'fc_a')}{ordinals[pri[-1]]} {de_primaria}")
        else:
            parts.append(", ".join(ordinals[c] for c in pri[:-1]) + f"{t(lang, 'fc_i')}{ordinals[pri[-1]]} {de_primaria}")
    return " · ".join(parts)


def ordre_edat(codes):
    """Índex del curs més menut de la fitxa (0 = 3 anys ... 8 = 6é); 99 si no
    declara cursos — així "Ordena per edat" les deixa al final."""
    ordre = [c for c, _, _ in NIVELLS]
    idx = [ordre.index(c) for c in (codes or []) if c in ordre]
    return min(idx) if idx else 99


def filtre_cursos_html(lang):
    """Desplegable "Filtrar per curs: <curs>" de la landing (orde sempre
    alfabètic, decisió Jorge 28-ago). Filtra i reordena les tarjetes en el
    navegador (sense recarregar) a partir dels atributs data-cursos /
    data-nom / data-ordre-edat de cada tarjeta. Les tarjetes amb
    data-cursos="*" (bloc municipal, o activitat que no declara cursos) es
    veuen sempre; el bloc municipal es queda sempre a l'últim."""
    opts = "\n".join(f'    <option value="{c}">{nivell_label(c, lang)}</option>' for c, _, _ in NIVELLS)
    singular = t(lang, "filtre_extraescolar_singular")
    plural = t(lang, "filtre_extraescolars_plural")
    return f"""<div class="filtre-cursos">
  <label for="filtre-curs">{t(lang, "filtre_label")}</label>
  <select id="filtre-curs">
    <option value="">{t(lang, "filtre_totes")}</option>
{opts}
  </select>
  <span class="filtre-compte" id="filtre-compte" aria-live="polite"></span>
</div>
<script>
// S'executa quan el DOM està carregat: el <script> va ABANS del grid i, si no, el grid encara no existix (bug 28-ago).
document.addEventListener('DOMContentLoaded', function () {{
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
    compte.textContent = v ? (n + ' ' + (n === 1 ? '{singular}' : '{plural}')) : '';
    var llista = cards.slice();
    llista.sort(function (a, b) {{
      var fa = a.hasAttribute('data-fixa-final') ? 1 : 0, fb = b.hasAttribute('data-fixa-final') ? 1 : 0;
      if (fa !== fb) return fa - fb;
      return a.getAttribute('data-nom') < b.getAttribute('data-nom') ? -1 : 1;
    }});
    llista.forEach(function (c) {{ grid.appendChild(c); }});
  }}
  sel.addEventListener('change', aplica);
}});
</script>"""


def card_attrs(a, clau, fixa_final=False):
    """Atributs data-* d'una tarjeta de la landing (vore filtre_cursos_html)."""
    cursos = a.get("cursos") or []
    data_cursos = " ".join(cursos) if (cursos and not fixa_final) else "*"
    attrs = f' data-cursos="{data_cursos}" data-nom="{clau}" data-ordre-edat="{ordre_edat(cursos)}"'
    if fixa_final:
        attrs += ' data-fixa-final="1"'
    return attrs


def cursos_html(a, lang):
    txt_cursos = format_cursos(a.get("cursos"), lang)
    return f'<p class="fitxa-cursos"><strong>{t(lang, "cursos_label")}</strong> {txt_cursos}</p>' if txt_cursos else ""


def empresa_html(a, lang):
    e = txt(a, "empresa", lang)
    return f'<p class="fitxa-empresa">{t(lang, "empresa_label")} <strong>{e}</strong></p>' if e else ""


def form_link_html(url, label, lang):
    if url:
        return (f'<a class="recurs" href="{url}" target="_blank" rel="noreferrer noopener">'
                f'<span class="icona">📝</span> {label}</a>')
    return (f'<span class="recurs recurs-pendent"><span class="icona">📝</span> {label}: '
            f'{t(lang, "pendent")}</span>')


# --------------------------------------------------------------------------
# Visibilitat de pàgines/seccions (04-09-2026): dos interruptors independents
# perquè la junta puga "amagar" contingut mentre el prepara, sense esborrar
# res ni tocar codi:
#   - `visible` (camp booleà per pàgina, a content/pagines/*.yml): si és
#     False, la pàgina desapareix del menú i del peu i s'escriu com a STUB
#     (mateixa capçalera/peu, cos = avís "en preparació"), mai un 404 — els
#     enllaços ja compartits no trenquen.
#   - `extraescolars_visibles` (content/web.yml): interruptor global de tota
#     la secció Extraescolars (vore load_web() i pagina_extraescolars_stub()).
# Absència del fitxer/camp = comportament d'abans (tot visible).
# --------------------------------------------------------------------------
def _es_fals(v):
    """Interpreta com a "fals" el booleà False i també els textos escrits a mà
    "false"/"no"/"0"/"off" (Pages CMS escriu booleans reals; editant el YAML a
    mà des de GitHub pot arribar amb cometes). Qualsevol altra cosa = visible:
    davant el dubte es publica, no s'amaga."""
    if isinstance(v, str):
        return v.strip().lower() in {"false", "no", "0", "off"}
    return v is False or v == 0


PAGINES_SLUGS = {"qui-som", "fes-te-de-lafa", "contacte", "mes-que-verd", "estatuts", "conciliacio"}

_pagina_visible_cache = {}
_web_cache = None


def pagina_visible(slug):
    """Torna False només si content/pagines/{slug}.yml existix i porta
    `visible: false` explícit. Absència del camp (fitxes actuals de la
    junta, que no el porten) = True. Cachejat perquè es consulta múltiples
    voltes (nav, peu, home) per la mateixa pàgina."""
    if slug not in _pagina_visible_cache:
        try:
            d = load_yaml(f"pagines/{slug}.yml") or {}
        except FileNotFoundError:
            d = {}
        _pagina_visible_cache[slug] = not _es_fals(d.get("visible", True))
    return _pagina_visible_cache[slug]


def load_web():
    """Carrega content/web.yml (interruptor global de la secció
    Extraescolars). Si el fitxer no existix o està buit: secció visible i
    avisos per defecte (el mateix text que porta el fitxer inicial)."""
    global _web_cache
    if _web_cache is None:
        try:
            w = load_yaml("web.yml") or {}
        except FileNotFoundError:
            w = {}
        _web_cache = {
            "extraescolars_visibles": not _es_fals(w.get("extraescolars_visibles", True)),
            "extraescolars_avis": w.get("extraescolars_avis") or (
                "Estem preparant la informació de les extraescolars del curs 2026-27. "
                "Prompte estarà disponible."
            ),
            "extraescolars_avis_es": w.get("extraescolars_avis_es") or (
                "Estamos preparando la información de las extraescolares del curso 2026-27. "
                "Pronto estará disponible." if not w else None
            ),
        }
    return _web_cache


def href_visible(href):
    """Torna False si `href` apunta a una pàgina de content/pagines/ marcada
    `visible: false`, o a "extraescolars/index.html" i la secció sencera
    està oculta (content/web.yml). Per a qualsevol altre href (junta, blog,
    galeria...) torna sempre True. Font única per a nav, peu i home."""
    if href == "extraescolars/index.html":
        return load_web()["extraescolars_visibles"]
    if href.endswith(".html") and "/" not in href:
        slug = href[:-len(".html")]
        if slug in PAGINES_SLUGS:
            return pagina_visible(slug)
    return True


# --------------------------------------------------------------------------
# Menú i plantilla comuna (idèntics als del clon original — no és contingut
# editable per la junta, viu ací com a codi). Les etiquetes es tradueixen amb
# `t(lang, clau)`; els `href` NO canvien amb l'idioma (l'arbre /es/ és un
# espill exacte de l'arrel, mateixos noms de fitxer).
# --------------------------------------------------------------------------
NAV = [
    {"key": "nav_afa", "children": [
        ("qui-som.html", "nav_lafa"),
        ("fes-te-de-lafa.html", "nav_fes_membre"),
        ("junta.html", "nav_junta"),
        ("estatuts.html", "nav_estatuts"),
    ]},
    {"key": "nav_extraescolars", "href": "extraescolars/index.html"},
    {"key": "nav_conciliacio", "href": "conciliacio.html"},
    {"key": "nav_noticies", "children": [
        ("blog/index.html", "nav_blog"),
        ("galeria.html", "nav_galeria"),
    ]},
    {"key": "nav_projectes", "children": [
        ("mes-que-verd.html", "nav_mes_que_verd"),
    ]},
    {"key": "nav_contacte", "href": "contacte.html"},
    {"key": "nav_fes_membre", "href": "fes-te-de-lafa.html"},
    {"key": "nav_web_escola", "href": "https://portal.edu.gva.es/46028430/", "extern": True},
]

FOOTER_LINKS_SECUNDARIS = [
    ("mes-que-verd.html", "nav_mes_que_verd"),
    ("blog/index.html", "nav_blog"),
]


def build_nav_html(lang, depth, active_href):
    parts = []
    for item in NAV:
        if "children" in item:
            children = [(h, key) for h, key in item["children"] if href_visible(h)]
            if not children:
                continue  # el grup es queda sense fills visibles → s'omet sencer
            child_hrefs = [h for h, _ in children]
            parent_actiu = " actiu" if active_href in child_hrefs else ""
            children_html = "\n        ".join(
                f'<li><a class="submenu-item{" actiu" if h == active_href else ""}" '
                f'href="{rel(depth, h)}">{t(lang, key)}</a></li>'
                for h, key in children
            )
            parts.append(f"""<div class="menu-item-parent">
        <button type="button" class="menu-item menu-toggle{parent_actiu}" aria-expanded="false" aria-haspopup="true" onclick="
          var s=this.nextElementSibling; var o=s.classList.toggle('obert'); this.setAttribute('aria-expanded', o);
        ">{t(lang, item["key"])} <span class="caret" aria-hidden="true"><svg width="11" height="7" viewBox="0 0 11 7" fill="none"><path d="M1 1l4.5 4.5L10 1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span></button>
        <ul class="submenu">
        {children_html}
        </ul>
      </div>""")
        else:
            href = item["href"]
            extern = item.get("extern")
            if not extern and not href_visible(href):
                continue
            full_href = href if extern else rel(depth, href)
            is_actiu = " actiu" if href == active_href else ""
            target_attrs = ' target="_blank" rel="noreferrer noopener"' if extern else ""
            parts.append(f'<a class="menu-item{is_actiu}" href="{full_href}"{target_attrs}>{t(lang, item["key"])}</a>')
    return "\n      ".join(parts)


def render_page(*, lang, depth, page_path, active_href, title, meta_desc, body_html, noindex=False):
    """`depth` = profunditat LOCAL de la pàgina dins del seu propi arbre
    (0 = arrel, 1 = blog/extraescolars...). `page_path` = ruta de la pàgina
    relativa a l'arrel de qualsevol dels dos arbres (p. ex. "index.html",
    "blog/2026-06-04-post.html") — el mateix camí existix a l'arrel (va) i a
    `es/` (es), és la clau per a calcular la bessona d'idioma i el hreflang.
    `noindex=True` força la meta robots encara que no siga build PREVIEW —
    l'usen les pàgines/seccions ocultes (stub "en preparació")."""
    ad = depth + ROOT_OFFSET[lang]  # profunditat per a arribar a assets/ (només a l'arrel de dist/)
    css = rel(ad, "assets/css/style.css")
    logo = rel(ad, "assets/img/logo-afa.png")
    home = rel(depth, "index.html")
    nav_html = build_nav_html(lang, depth, active_href)
    footer_extra = "\n            ".join(
        f'<li><a href="{rel(depth, href)}">{t(lang, key)}</a></li>'
        for href, key in FOOTER_LINKS_SECUNDARIS if href_visible(href)
    )
    footer_web_links = [
        (h, key) for h, key in [
            ("qui-som.html", "nav_lafa"),
            ("extraescolars/index.html", "nav_extraescolars"),
            ("conciliacio.html", "nav_conciliacio"),
        ] if href_visible(h)
    ]
    footer_web_html = "\n          ".join(
        f'<li><a href="{rel(depth, h)}">{t(lang, key)}</a></li>' for h, key in footer_web_links
    )
    contacte_li = (f'<li><a href="{rel(depth, "contacte.html")}">{t(lang, "footer_mes_contacte")}</a></li>'
                   if href_visible("contacte.html") else "")
    head_extra = '<meta name="robots" content="noindex, nofollow">' if (PREVIEW or noindex) else ""

    a_href = alt_href(lang, depth, page_path)
    html_lang = "es" if lang == "es" else "ca"
    abs_va = f"https://{DOMINI}/{page_path}"
    abs_es = f"https://{DOMINI}/es/{page_path}"

    # Preferència d'idioma (localStorage 'afa-lang'): si l'usuari ja va triar
    # abans un idioma diferent al d'esta pàgina, el porta directament a la
    # seua bessona — el destí SEMPRE coincidix amb la preferència, no pot
    # entrar en bucle. El selector de la capçalera fixa la preferència ABANS
    # de navegar (onclick), este script només actua en visites posteriors.
    pref_script = (
        "<script>(function(){try{var p=localStorage.getItem('afa-lang');"
        f"if(p&&p!=='{lang}')location.replace('{a_href}');"
        "}catch(e){}})();</script>"
    )

    if lang == "va":
        val_href, val_cls, val_onclick = "#", " actiu", ""
        cast_href, cast_cls = a_href, ""
        cast_onclick = " onclick=\"try{localStorage.setItem('afa-lang','es')}catch(e){}\""
    else:
        val_href, val_cls = a_href, ""
        val_onclick = " onclick=\"try{localStorage.setItem('afa-lang','va')}catch(e){}\""
        cast_href, cast_cls, cast_onclick = "#", " actiu", ""
    lang_switch_html = f"""<div class="lang-switch">
      <a href="{val_href}" class="lang-link{val_cls}"{val_onclick}>{t(lang, "lang_val")}</a>
      <span class="lang-sep" aria-hidden="true">|</span>
      <a href="{cast_href}" class="lang-link{cast_cls}"{cast_onclick}>{t(lang, "lang_cast")}</a>
    </div>"""

    # Open Graph (04-09-2026, SEO): mateix títol/descripció que ja es calculen
    # per a <title>/<meta description>, imatge fixa per a tot el lloc:
    # assets/img/og-afa.jpg (1200×630, retall de la il·lustració de portada —
    # dibuix, sense menors). El logo (204×343) era massa menut: WhatsApp i
    # Facebook no mostren imatges de menys de ~300 px. og:url apunta a la
    # bessona d'idioma correcta.
    titol_complet = f"{title} · AFA CEIP Alejandra Soler"
    og_url = abs_va if lang == "va" else abs_es
    og_locale = "ca_ES" if lang == "va" else "es_ES"
    og_image = f"https://{DOMINI}/assets/img/og-afa.jpg"

    def _og_esc(s):
        return s.replace('"', "&quot;")

    og_html = f"""<meta property="og:type" content="website">
<meta property="og:site_name" content="AFA CEIP Alejandra Soler">
<meta property="og:title" content="{_og_esc(titol_complet)}">
<meta property="og:description" content="{_og_esc(meta_desc)}">
<meta property="og:url" content="{og_url}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{og_locale}">"""

    html_out = f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>{head_extra}
{pref_script}
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titol_complet}</title>
<meta name="description" content="{meta_desc}">
<link rel="icon" href="{logo}">
<link rel="alternate" hreflang="ca" href="{abs_va}">
<link rel="alternate" hreflang="es" href="{abs_es}">
<link rel="alternate" hreflang="x-default" href="{abs_va}">
{og_html}
<link rel="stylesheet" href="{css}">
</head>
<body>

<header class="site-header">
  <div class="wrap">
    <a class="marca" href="{home}">
      <img src="{logo}" alt="{t(lang, "logo_alt")}" width="44" height="74">
      <span>AFA CEIP Alejandra Soler<small>{t(lang, "marca_subtitle")}</small></span>
    </a>
    {lang_switch_html}
    <button class="nav-toggle" aria-expanded="false" aria-controls="menu-principal" onclick="
      var n=document.getElementById('menu-principal');
      var obert = n.classList.toggle('obert');
      this.setAttribute('aria-expanded', obert);
    ">{t(lang, "menu_toggle")}</button>
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
        <h4>{t(lang, "footer_afa_title")}</h4>
        <ul>
          <li>{t(lang, "footer_russafa")}</li>
          <li><a href="mailto:secretariaalejandrasoler@gmail.com">secretariaalejandrasoler@gmail.com</a></li>
          {contacte_li}
        </ul>
      </div>
      <div>
        <h4>{t(lang, "footer_web_title")}</h4>
        <ul>
          {footer_web_html}
          {footer_extra}
        </ul>
      </div>
      <div>
        <h4>{t(lang, "footer_enllacos_title")}</h4>
        <ul>
          <li><a href="https://portal.edu.gva.es/46028430/" target="_blank" rel="noreferrer noopener">{t(lang, "footer_web_escola")}</a></li>
          <li><a href="https://www.aulazon.es/categoria-producto/colegios/ceip-alejandra-soler/ampa-afa-ceip-alejandra-soler/" target="_blank" rel="noreferrer noopener">{t(lang, "footer_pagament")}</a></li>
        </ul>
      </div>
    </div>
    <div class="avall">
      <span>{t(lang, "footer_copyright")}</span>
    </div>
  </div>
</footer>

</body>
</html>
"""
    # Fix rutes absolutes "/assets/..." dins del cos (04-09-2026): cos_html()
    # i les rutes que escriu Pages CMS des dels camps `media` normalitzen
    # sempre a "/assets/..." (absolut des de l'arrel del domini — vore
    # cos_html()). En producció (dist/ a l'arrel del domini) això funciona,
    # però en la preview (GitHub Pages en una SUBRUTA, /afa-web-preview/)
    # trenca en 404. Ho reescrivim ací, en el HTML JA assemblat, a la ruta
    # relativa correcta per a esta pàgina (`rel(ad, "assets/")` — la mateixa
    # profunditat que ja s'usa per a css/logo). Enllaços externs i mailto:
    # no es toquen (el regex només actua sobre "/assets/" literal).
    html_out = _ASSET_ABS_RE.sub(lambda m: f'{m.group(1)}="{rel(ad, "assets/")}', html_out)

    # Registre per al sitemap (vore SITEMAP_ENTRIES més amunt): NOMÉS les
    # pàgines de veres indexables — mai en build PREVIEW, ni les que porten
    # noindex (stubs de pàgina oculta o de la secció Extraescolars oculta).
    if not PREVIEW and not noindex:
        SITEMAP_ENTRIES.append((lang, page_path))

    return html_out


def write(relpath, html):
    full = os.path.join(DIST, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)
    print("escrit:", relpath)


def asset_link(url, label, depth, icon="📄"):
    href = local_asset_href(depth, url)
    return f'<a class="recurs" href="{href}" target="_blank" rel="noreferrer noopener"><span class="icona">{icon}</span> {label}</a>'


def portada_img_html(depth, imatge_path, alt, lang):
    """`imatge_path` ve del camp `imatge` del YAML (ruta relativa dins del
    repo, p. ex. assets/img/portades/judo.png), o None si no n'hi ha.
    `depth` ja ha de portar sumat ROOT_OFFSET[lang] (profunditat d'assets)."""
    if not imatge_path:
        return None
    href = local_asset_href(depth, imatge_path)
    if imatge_path.endswith(".png"):
        return f'<img class="portada-logo" src="{href}" alt="{t(lang, "portada_logo_alt_prefix")} {alt}" loading="lazy">'
    return f'<img src="{href}" alt="{alt}" loading="lazy">'


# --------------------------------------------------------------------------
# Pàgina: INDEX (home) — no editable per la junta en v1 (fora d'abast, veure
# README.md "Per a la junta"). Contingut fix, igual que el clon original.
# --------------------------------------------------------------------------

def pagina_home(lang):
    ad = ROOT_OFFSET[lang]
    portada_href = local_asset_href(ad, "https://ampaalejandrasoler.es/wp-content/uploads/2022/09/Portada_Web_22_23.png")

    # Tarjetes «accio»: s'omet la d'Extraescolars si la secció està oculta
    # (content/web.yml) i la de Qui som si la pàgina està oculta (visible:
    # false a content/pagines/qui-som.yml) — mateixa font que el menú/peu.
    cards = []
    if href_visible("extraescolars/index.html"):
        cards.append(f"""    <a class="accio" href="extraescolars/index.html">
      <h3>{t(lang, "home_card1_title")}</h3>
      <p>{t(lang, "home_card1_desc")}</p>
    </a>""")
    cards.append(f"""    <a class="accio" href="blog/index.html">
      <h3>{t(lang, "home_card2_title")}</h3>
      <p>{t(lang, "home_card2_desc")}</p>
    </a>""")
    if href_visible("qui-som.html"):
        cards.append(f"""    <a class="accio" href="qui-som.html">
      <h3>{t(lang, "home_card3_title")}</h3>
      <p>{t(lang, "home_card3_desc")}</p>
    </a>""")
    if href_visible("contacte.html"):
        cards.append(f"""    <a class="accio" href="contacte.html">
      <h3>{t(lang, "home_card4_title")}</h3>
      <p>{t(lang, "home_card4_desc")}</p>
    </a>""")
    cards_html = "\n".join(cards)

    body = f"""
<section class="hero">
  <div class="wrap">
    <span class="eyebrow">{t(lang, "home_eyebrow")}</span>
    <h1>{t(lang, "home_h1")}</h1>
  </div>
</section>

<div class="wrap">

<section>
  <img class="imatge-doc" src="{portada_href}" alt="{t(lang, "home_portada_alt")}" loading="lazy">
</section>

<section>
  <div class="grid-accions">
{cards_html}
  </div>
</section>

</div>
"""
    return render_page(
        lang=lang, depth=0, page_path="index.html", active_href="index.html",
        title=t(lang, "home_title"),
        meta_desc=t(lang, "home_meta_desc"),
        body_html=body,
    )


# --------------------------------------------------------------------------
# Pàgines estàtiques (content/pagines/*.yml)
# --------------------------------------------------------------------------

def pagina_estatica(slug, lang):
    d = load_yaml(f"pagines/{slug}.yml")
    title = txt(d, "titol_pestanya", lang) or txt(d, "titol", lang)

    if not pagina_visible(slug):
        # STUB (04-09-2026): la pàgina existix igual (mateixa capçalera/peu i
        # títol), però el cos és només l'avís "en preparació" — mai un 404,
        # perquè enllaços ja compartits no trenquen.
        body = f"""
<div class="wrap"><section><h1>{txt(d, "titol", lang)}</h1><p class="nota">{t(lang, "pagina_en_preparacio")}</p></section></div>
"""
        return render_page(
            lang=lang, depth=0, page_path=f"{slug}.html", active_href=f"{slug}.html",
            title=title, meta_desc=txt(d, "meta_desc", lang), body_html=body,
            noindex=True,
        )

    body = f"""
<div class="page-hero"><div class="wrap"><h1>{txt(d, "titol", lang)}</h1><p>{txt(d, "subtitol", lang)}</p></div></div>
<div class="wrap">
<section>
{cos_html(txt(d, "cos", lang))}
</section>
</div>
"""
    return render_page(
        lang=lang, depth=0, page_path=f"{slug}.html", active_href=f"{slug}.html",
        title=title, meta_desc=txt(d, "meta_desc", lang), body_html=body,
    )


# --------------------------------------------------------------------------
# Junta (content/junta/*.yml)
# --------------------------------------------------------------------------

def pagina_junta(lang):
    ad = ROOT_OFFSET[lang]
    membres = load_collection("junta")
    membres.sort(key=lambda m: m.get("ordre", 999))
    comissions = load_yaml("junta/_comissions.yml")["comissions"]

    membres_html = []
    for m in membres:
        img = local_asset_href(ad, m["imatge"])
        email_html = (f'<p class="fitxa-meta"><a href="mailto:{m["email"]}">{m["email"]}</a></p>'
                      if m.get("email") else "")
        # 'nom' (nom i cognoms de la persona) NO es tradueix — dada personal.
        membres_html.append(f"""<div class="wp-media-text">
  <img src="{img}" alt="" width="100" height="100" loading="lazy">
  <div><p>{txt(m, "carrec", lang)}: <strong>{m['nom']}</strong></p>{email_html}</div>
</div>""")
    membres_html = "\n".join(membres_html)

    # 'contacte' (nom de pila de la persona voluntària) NO es tradueix.
    comissions_html = "\n".join(
        f'<li><strong>{txt(c, "nom", lang)}</strong> — {t(lang, "junta_contacte_prefix")}{c["contacte"]}</li>' for c in comissions
    )

    body = f"""
<div class="page-hero"><div class="wrap"><h1>{t(lang, "junta_h1")}</h1><p>{t(lang, "junta_subtitle")}</p></div></div>
<div class="wrap">
<section>
<div class="junta-llista">
{membres_html}
</div>

<h2>{t(lang, "junta_comissions_h2")}</h2>
<ul>
{comissions_html}
</ul>
<p><strong>{t(lang, "junta_participa_h")}</strong></p>
<p>{t(lang, "junta_participa_p")}</p>
</section>
</div>
"""
    return render_page(
        lang=lang, depth=0, page_path="junta.html", active_href="junta.html",
        title=t(lang, "junta_h1"),
        meta_desc=t(lang, "junta_meta_desc"),
        body_html=body,
    )


# --------------------------------------------------------------------------
# Blog (content/blog/*.yml)
# --------------------------------------------------------------------------

def pagina_blog_index(posts, lang):
    cards = []
    for p in posts:
        cards.append(f"""<a class="post-card" href="{p['_slug']}.html">
  <time datetime="{p['data']}">{txt(p, "data_label", lang)}</time>
  <h3>{txt(p, "titol", lang)}</h3>
</a>""")
    cards_html = "\n".join(cards)
    body = f"""
<div class="page-hero"><div class="wrap"><h1>{t(lang, "blog_h1")}</h1><p>{t(lang, "blog_subtitle")}</p></div></div>
<div class="wrap">
<section>
<div class="post-llista">
{cards_html}
</div>
</section>
</div>
"""
    return render_page(
        lang=lang, depth=1, page_path="blog/index.html", active_href="blog/index.html",
        title=t(lang, "blog_h1"),
        meta_desc=t(lang, "blog_meta_desc"),
        body_html=body,
    )


def pagina_blog_post(p, lang):
    ad = 1 + ROOT_OFFSET[lang]
    titol = txt(p, "titol", lang)
    data_label = txt(p, "data_label", lang)
    # CAS ESPECIAL (02-09-2026): l'arbre va mostra NOMÉS cos_valencia (ja no
    # el castellà incrustat davall); l'arbre es mostra cos_castella, i si no
    # existix encara, cau a cos_valencia — mai una pàgina buida.
    cos = p.get("cos_valencia") if lang == "va" else (p.get("cos_castella") or p.get("cos_valencia"))

    imatge_html = ""
    if p.get("imatge"):
        img_href = local_asset_href(ad, p["imatge"])
        imatge_html = f'<img class="imatge-doc" src="{img_href}" alt="{titol}" loading="lazy">'
    body = f"""
<div class="wrap">
<article>
<p class="fitxa-meta"><time datetime="{p['data']}">{data_label}</time> · AFA CEIP Alejandra Soler</p>
<h1>{titol}</h1>
<div class="post-cos">
{cos_html(cos)}
</div>
{imatge_html}
<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="index.html">{t(lang, "blog_back")}</a>
</div>
</article>
</div>
"""
    return render_page(
        lang=lang, depth=1, page_path=f"blog/{p['_slug']}.html", active_href="blog/index.html",
        title=titol,
        meta_desc=f"{titol}{t(lang, 'blog_post_meta_desc_suffix')}",
        body_html=body,
    )


# --------------------------------------------------------------------------
# Galeria — fora d'abast de l'editor v1 (contingut fix, igual que el clon).
# Cada foto porta alt-text va + es.
# --------------------------------------------------------------------------
GALERIA_FOTOS = [
    ("2014/11/ampa100_0016__PLG6242.jpg", "Carrer del col·legi", "Calle del colegio"),
    ("2014/11/ampa100_0009__PLG6116.jpg", "Pati, vista des de dalt", "Patio, vista desde arriba"),
    ("2014/11/ampa100_0008__PLG6120.jpg", "Pati d'Infantil", "Patio de Infantil"),
    ("2014/11/ampa100_0005__PLG6092.jpg", "Passadís de l'escola", "Pasillo de la escuela"),
    ("2014/11/ampa100_0013__PLG6191.jpg", "Pati poliesportiu", "Patio polideportivo"),
    ("2014/11/ampa100_0001__PLG6109.jpg", "Aula", "Aula"),
    ("2014/11/ampa100_0003__PLG6106.jpg", "Aula amb pissarra", "Aula con pizarra"),
    ("2014/03/banner-infantil1.jpg", "Edifici i pati d'Infantil", "Edificio y patio de Infantil"),
]


def pagina_galeria(lang):
    ad = ROOT_OFFSET[lang]
    items = []
    for url, alt_va, alt_es in GALERIA_FOTOS:
        href = local_asset_href(ad, "https://ampaalejandrasoler.es/wp-content/uploads/" + url)
        alt = alt_va if lang == "va" else alt_es
        items.append(
            f'<a class="galeria-item" href="{href}" target="_blank" rel="noreferrer noopener">'
            f'<img src="{href}" alt="{alt}" loading="lazy"></a>'
        )
    fotos_grid = "\n".join(items)
    body = f"""
<div class="page-hero"><div class="wrap"><h1>{t(lang, "galeria_h1")}</h1><p>{t(lang, "galeria_subtitle")}</p></div></div>
<div class="wrap">
<section>
<div class="grid-galeria">
{fotos_grid}
</div>
</section>
</div>
"""
    return render_page(
        lang=lang, depth=0, page_path="galeria.html", active_href="galeria.html",
        title=t(lang, "galeria_h1"),
        meta_desc=t(lang, "galeria_meta_desc"),
        body_html=body,
    )


# --------------------------------------------------------------------------
# Extraescolars (content/extraescolars/*.yml — inclou activitats-municipals)
# --------------------------------------------------------------------------

def _clau_alfabetica(nom):
    s = unicodedata.normalize("NFD", nom)
    return "".join(c for c in s if not unicodedata.combining(c) and c not in "'’").lower()


# Valors per defecte de la secció "Horaris per curs" — s'usen només si
# content/horaris.yml no existix o té un camp buit. El fitxer editable des
# de Pages CMS és content/horaris.yml.
HORARI_GENERAL = "https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls.-Horari-2526-4_page-0001.jpg"
PREUS_MUNICIPALS = "https://ampaalejandrasoler.es/wp-content/uploads/2025/09/Informacio-actv-municipals_-preus-i-cursos.pdf"
HORARIS_NIVELL = [
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls.-3-anys_page-0001.jpg", "3 anys", "3 años"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0010.jpg", "4 anys", "4 años"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0011.jpg", "5 anys", "5 años"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0012.jpg", "1er Primària", "1er Primaria"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0013.jpg", "2n Primària", "2º Primaria"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2026/01/Horari-i-espais-2025-2026xls._pages-to-jpg-0014.jpg", "3er Primària", "3er Primaria"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2025/09/Horari-i-espais-2025-2026xls.-4rt-prim_page-0001.jpg", "4t Primària", "4º Primaria"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2025/11/Horari-i-espais-2025-2026xls.-5e-prim_page-0001.jpg", "5é Primària", "5º Primaria"),
    ("https://ampaalejandrasoler.es/wp-content/uploads/2025/11/Horari-i-espais-2025-2026xls.-6e-prim_page-0001.jpg", "6é Primària", "6º Primaria"),
]


def load_horaris():
    """Carrega content/horaris.yml (editable des de Pages CMS). Torna un
    dict amb:
      nota / nota_es: string o None (None = usar el text fix t(lang, "extra_horaris_nota"))
      horari_general / preus_municipals: string (URL o ruta local) o None (sense enllaç)
      horaris_nivell: llista de tuples (url, curs_va, curs_es)

    Dos xarxes de seguretat DIFERENTS (perquè un oblit de la junta mai trenca
    el build, però buidar un recurs a propòsit sí que l'ha de fer desaparéixer):
      - Si el FITXER SENCER no existix o està buit (encara no s'ha creat/
        editat des de l'editor), es cau als valors originals de la migració
        (constants HORARI_GENERAL / PREUS_MUNICIPALS / HORARIS_NIVELL).
      - Si el fitxer SÍ existix: `horari_general` i `preus_municipals` són
        recursos individuals — si la junta els buida a propòsit des de
        l'editor, es tracten com None (recursos_html ho omet, no torna a
        mostrar el recurs antic). `horaris_nivell` és una llista: les
        entrades sense `imatge` o sense `curs` s'ometen en silenci, però si
        la llista sencera queda buida (l'editor no en té cap), es cau a la
        constant per no deixar la secció «Horari per nivell/curs» buida.
    """
    try:
        h = load_yaml("horaris.yml") or {}
    except FileNotFoundError:
        h = {}

    if not h:
        return {
            "nota": None,
            "nota_es": None,
            "horari_general": HORARI_GENERAL,
            "preus_municipals": PREUS_MUNICIPALS,
            "horaris_nivell": HORARIS_NIVELL,
        }

    nivells = []
    for entrada in h.get("horaris_nivell") or []:
        if not isinstance(entrada, dict):
            continue
        imatge = entrada.get("imatge")
        curs = entrada.get("curs")
        if not imatge or not curs:
            continue
        nivells.append((imatge, curs, entrada.get("curs_es") or curs))

    return {
        "nota": h.get("nota") or None,
        "nota_es": h.get("nota_es") or None,
        "horari_general": h.get("horari_general") or None,
        "preus_municipals": h.get("preus_municipals") or None,
        "horaris_nivell": nivells or HORARIS_NIVELL,
    }


_extra_textos_cache = None


def load_extra_textos():
    """Carrega content/extraescolars-textos.yml (04-09-2026): títol, subtítol,
    els 4 paràgrafs d'introducció, el text del botó de places, la nota dels
    asteriscs i l'apartat Baixes de la LANDING d'Extraescolars — abans fixos
    al diccionari `T`, ara editables des de Pages CMS. Cachejat. Si el fitxer
    no existix o està buit, torna {} i cada camp cau al seu valor fix de `T`
    (vore pagina_extraescolars_landing) — mai la pàgina a mitges."""
    global _extra_textos_cache
    if _extra_textos_cache is None:
        try:
            _extra_textos_cache = load_yaml("extraescolars-textos.yml") or {}
        except FileNotFoundError:
            _extra_textos_cache = {}
    return _extra_textos_cache


_NOTA_P_RE = re.compile(r"<p>(.*)</p>", re.S)


def pagina_extraescolars_landing(activitats, lang):
    ad = 1 + ROOT_OFFSET[lang]
    h = load_horaris()
    et = load_extra_textos()

    # Textos de la landing (04-09-2026): camp buit/fitxer absent → text fix
    # de T (idèntic al comportament d'abans). `txt()` ja resol el fallback
    # _es → valencià dins del propi YAML; l'`or` de fora resol YAML buit → T.
    titol = txt(et, "titol", lang) or t(lang, "extra_h1")
    subtitol = txt(et, "subtitol", lang) or t(lang, "extra_subtitle")
    boto_places = txt(et, "boto_places", lang) or t(lang, "extra_btn_places")
    asteriscs_nota = txt(et, "asteriscs_nota", lang) or t(lang, "extra_asteriscs_nota")
    baixes_titol = txt(et, "baixes_titol", lang) or t(lang, "extra_baixes_h3")

    def _intro_html(camp, clau_t):
        """cos_html() ja envolta un paràgraf pla en <p>...</p> — EXACTAMENT
        el mateix marcatge que hi havia fix ('<p>{t(...)}</p>'), i deixa
        passar l'HTML inline (<a href...>) que porten intro2/intro4 —
        verificat 0 diferències amb el contingut actual (docs/REGISTRO_TECNIC.md
        04-09-2026)."""
        valor = txt(et, camp, lang)
        return cos_html(valor) if valor else f'<p>{t(lang, clau_t)}</p>'

    intro1_html = _intro_html("intro1", "extra_intro1")
    intro2_html = _intro_html("intro2", "extra_intro2")
    intro3_html = _intro_html("intro3", "extra_intro3")
    intro4_html = _intro_html("intro4", "extra_intro4")

    # Baixes: el marcatge ORIGINAL és '<p class="nota">{text}</p>' (amb
    # classe — a diferència dels intros), així que la classe es deixa FIXA
    # ací i només s'hi insereix el contingut. Per al cas normal (un sol
    # paràgraf, com el text migrat) cos_html() torna '<p>...</p>' — es lleva
    # eixe embolcall per a no duplicar <p><p>...</p></p>; si en el futur la
    # junta escriu diversos paràgrafs des del rich-text, es deixen tal qual
    # dins de la mateixa caixa "nota" (no és HTML perfecte, però no trenca
    # el navegador ni deixa la secció buida).
    baixes_valor = txt(et, "baixes_text", lang)
    if baixes_valor:
        _html = cos_html(baixes_valor)
        _m = _NOTA_P_RE.fullmatch(_html)
        # Un sol paràgraf (cas normal) → <p class="nota">; blocs (títol, llista...) → <div class="nota">
        baixes_html = (f'<p class="nota">{_m.group(1)}</p>' if _m else f'<div class="nota">{_html}</div>')
    else:
        baixes_html = f'<p class="nota">{t(lang, "extra_baixes_p")}</p>'

    def _card(a, fixa_final=False):
        nom = txt(a, "nom", lang)
        empresa = txt(a, "empresa", lang) or ""
        img_html = portada_img_html(ad, a.get("imatge"), alt=nom, lang=lang)
        # El bloc municipal mostra "FDM" (com el clon original), no les inicials
        inicials = "FDM" if fixa_final else initials(nom)
        visual = img_html if img_html else f'<div class="placeholder-img {a["ph"]}">{inicials}</div>'
        return f"""<a class="card-extra" href="{a['_slug']}.html"{card_attrs(a, _clau_alfabetica(nom), fixa_final=fixa_final)}>
  {visual}
  <div class="nom">{nom}<small class="empresa">{empresa}</small></div>
</a>"""

    # Les activitats es mostren per orde alfabètic (segons el nom en l'idioma
    # actual); "Activitats municipals (FDM)" es queda sempre AL FINAL (no és
    # una empresa, és un bloc apart), clon fiel del comportament original. El
    # desplegable de la landing pot reordenar-les per edat al navegador
    # (vore filtre_cursos_html).
    cards = [_card(a) for a in sorted(activitats, key=lambda a: _clau_alfabetica(txt(a, "nom", lang)))]
    grid = "\n".join(cards)

    horaris_grid = "\n".join(
        f'<a class="horari-item" href="{local_asset_href(ad, url)}" target="_blank" rel="noreferrer noopener">'
        f'<img src="{local_asset_href(ad, url)}" alt="{t(lang, "horari_alt_prefix")} {nv if lang == "va" else nes}" loading="lazy">'
        f'<span>{nv if lang == "va" else nes}</span></a>'
        for url, nv, nes in h["horaris_nivell"]
    )

    recursos = []
    if h["horari_general"]:
        recursos.append(asset_link(h["horari_general"], t(lang, "extra_horari_general_label"), ad))
    if h["preus_municipals"]:
        recursos.append(asset_link(h["preus_municipals"], t(lang, "extra_horaris_municipals_label"), ad))
    recursos_html = "\n".join(recursos)

    horaris_nota = txt(h, "nota", lang) if h["nota"] else t(lang, "extra_horaris_nota")

    body = f"""
<div class="page-hero"><div class="wrap"><h1>{titol}</h1>
<p>{subtitol}</p></div></div>
<div class="wrap">
<section>
{intro1_html}
{intro2_html}
{intro3_html}
{intro4_html}
<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="places-lliures.html">{boto_places}</a>
</div>
</section>

<section>
{filtre_cursos_html(lang)}
<div class="grid-extraescolars">
{grid}
</div>
</section>

<section>
<h2>{t(lang, "extra_horaris_h2")}</h2>
<p class="nota">{horaris_nota}</p>
<div class="recursos">
{recursos_html}
</div>
<p class="nota">{asteriscs_nota}</p>
<h3>{t(lang, "extra_horari_nivell_h3")}</h3>
<div class="grid-horaris">
{horaris_grid}
</div>
</section>

<section>
<h3>{baixes_titol}</h3>
{baixes_html}
</section>
</div>
"""
    return render_page(
        lang=lang, depth=1, page_path="extraescolars/index.html", active_href="extraescolars/index.html",
        title=t(lang, "nav_extraescolars"),
        meta_desc=t(lang, "extra_meta_desc"),
        body_html=body,
    )


def pagina_extraescolars_stub(lang):
    """Substitutiu de tota la secció Extraescolars quan
    content/web.yml porta `extraescolars_visibles: false` — mai s'escriuen
    ni la landing normal, ni places-lliures, ni cap fitxa (vore main())."""
    web = load_web()
    avis = txt(web, "extraescolars_avis", lang)
    body = f"""
<div class="wrap"><section><h1>{t(lang, "nav_extraescolars")}</h1><p class="nota">{avis}</p></section></div>
"""
    return render_page(
        lang=lang, depth=1, page_path="extraescolars/index.html", active_href="extraescolars/index.html",
        title=t(lang, "nav_extraescolars"),
        meta_desc=t(lang, "extra_meta_desc"),
        body_html=body,
        noindex=True,
    )


def pagina_activitat(a, lang):
    ad = 1 + ROOT_OFFSET[lang]
    nom = txt(a, "nom", lang)

    resources = [asset_link(a["dossier"], txt(a, "dossier_label", lang) or t(lang, "activitat_dossier_label"), ad)]
    if a.get("dossier2"):
        resources.append(asset_link(a["dossier2"], txt(a, "dossier2_label", lang) or t(lang, "activitat_dossier2_label"), ad))
    # Activitats municipals (FDM): la inscripció és per PDF (full + bonificació + preus),
    # no hi ha Google Form → no es mostra «pendent de publicar».
    for camp, etiqueta_key in (("inscripcio_pdf", "activitat_inscripcio_pdf_label"),
                               ("bonificacio", "activitat_bonificacio_label"),
                               ("info_preus", "activitat_info_preus_label")):
        if a.get(camp):
            resources.append(asset_link(a[camp], t(lang, etiqueta_key), ad))
    if a.get("form") or not a.get("inscripcio_pdf"):
        resources.append(form_link_html(a.get("form"), t(lang, "activitat_form_label"), lang))
    if a.get("form2"):
        resources.append(form_link_html(a["form2"], t(lang, "activitat_form2_label"), lang))
    resources_html = "\n".join(resources)

    nota = txt(a, "nota", lang)
    nota_html = f'<div class="avis">{cos_html(nota)}</div>' if nota else ""
    descripcio = txt(a, "descripcio", lang)
    descripcio_html = f'<div class="descripcio">{cos_html(descripcio)}</div>' if descripcio else ""

    fitxa_img_html = portada_img_html(ad, a.get("imatge"), alt=nom, lang=lang)
    fitxa_visual = fitxa_img_html if fitxa_img_html else f'<div class="placeholder-img {a["ph"]}">{initials(nom)}</div>'

    body = f"""
<div class="wrap">
<section>
<div class="fitxa-cap">
  {fitxa_visual}
  <div>
    <h1>{nom}</h1>
    <p class="fitxa-meta">{t(lang, "activitat_meta_line")}</p>
    {empresa_html(a, lang)}
    {cursos_html(a, lang)}
  </div>
</div>

{descripcio_html}

<div class="recursos">
{resources_html}
</div>

{nota_html}

<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="index.html">{t(lang, "activitat_back")}</a>
</div>
</section>
</div>
"""
    return render_page(
        lang=lang, depth=1, page_path=f"extraescolars/{a['_slug']}.html", active_href="extraescolars/index.html",
        title=nom,
        meta_desc=f"{nom}{t(lang, 'activitat_meta_desc_suffix')}",
        body_html=body,
    )


def pagina_places_lliures(lang):
    ad = 1 + ROOT_OFFSET[lang]
    d = load_yaml("places-lliures.yml")
    img_href = local_asset_href(ad, d["imatge"])
    body = f"""
<div class="wrap">
<section>
<h1>{t(lang, "places_h1")}</h1>
<p class="fitxa-meta">{t(lang, "places_subtitle")}</p>

<p>{t(lang, "places_intro")}</p>

<h2>{t(lang, "places_ultim_h2_prefix")}{txt(d, "mes_label", lang)}</h2>
<p class="nota">{t(lang, "places_nota")}</p>
<a class="horari-item horari-item-gran" href="{img_href}" target="_blank" rel="noreferrer noopener">
  <img class="imatge-doc" src="{img_href}" alt="{t(lang, "places_alt")}" loading="lazy">
  <span>{t(lang, "places_click_ampliar")}</span>
</a>

<h3>{t(lang, "places_llegenda_h3")}</h3>
<ul>
  <li>{t(lang, "places_li1")}</li>
  <li>{t(lang, "places_li2")}</li>
  <li>{t(lang, "places_li3")}</li>
  <li>{t(lang, "places_li4")}</li>
</ul>

<div class="botonera">
  <a class="boton boton-secundari boton-petit" href="index.html">{t(lang, "activitat_back")}</a>
</div>
</section>
</div>
"""
    return render_page(
        lang=lang, depth=1, page_path="extraescolars/places-lliures.html", active_href="extraescolars/index.html",
        title=t(lang, "places_h1"),
        meta_desc=t(lang, "places_meta_desc"),
        body_html=body,
    )


# --------------------------------------------------------------------------
# 404 (04-09-2026, SEO): GitHub Pages només llig `404.html` a l'ARREL del
# repo/domini i el servix per a QUALSEVOL ruta trencada, de QUALSEVOL
# profunditat. Les rutes relatives de render_page() (rel(), css, logo, nav...)
# es resoldrien contra la URL trencada del navegador, NO contra la ubicació
# real del fitxer — per això esta pàgina NO reutilitza render_page() i porta
# totes les seues rutes ABSOLUTES ("/assets/...", "/index.html"...) escrites
# a mà. Bilingüe en un sol fitxer (VA + ES), noindex, sense script de redirecció.
# --------------------------------------------------------------------------

def build_nav_html_abs(lang):
    """Versió del menú principal amb rutes ABSOLUTES ("/qui-som.html"...),
    usada NOMÉS per pagina_404(). Mateixa font (NAV, href_visible) que
    build_nav_html(), sense estat "actiu" (no té sentit en una pàgina d'error)."""
    parts = []
    for item in NAV:
        if "children" in item:
            children = [(h, key) for h, key in item["children"] if href_visible(h)]
            if not children:
                continue
            children_html = "\n        ".join(
                f'<li><a class="submenu-item" href="/{h}">{t(lang, key)}</a></li>'
                for h, key in children
            )
            parts.append(f"""<div class="menu-item-parent">
        <button type="button" class="menu-item menu-toggle" aria-expanded="false" aria-haspopup="true" onclick="
          var s=this.nextElementSibling; var o=s.classList.toggle('obert'); this.setAttribute('aria-expanded', o);
        ">{t(lang, item["key"])} <span class="caret" aria-hidden="true"><svg width="11" height="7" viewBox="0 0 11 7" fill="none"><path d="M1 1l4.5 4.5L10 1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span></button>
        <ul class="submenu">
        {children_html}
        </ul>
      </div>""")
        else:
            href = item["href"]
            extern = item.get("extern")
            if not extern and not href_visible(href):
                continue
            full_href = href if extern else f"/{href}"
            target_attrs = ' target="_blank" rel="noreferrer noopener"' if extern else ""
            parts.append(f'<a class="menu-item" href="{full_href}"{target_attrs}>{t(lang, item["key"])}</a>')
    return "\n      ".join(parts)


def pagina_404():
    """Pàgina 404 ÚNICA i bilingüe (dist/404.html). Mateixa capçalera/menú/peu
    i mateix CSS que la resta del lloc, però amb totes les rutes absolutes
    (vore comentari de dalt). Contingut: H1 + línia explicativa en cada
    idioma + enllaç a la portada VA i a la portada ES. Meta robots noindex."""
    css = "/assets/css/style.css"
    logo = "/assets/img/logo-afa.png"
    nav_html = build_nav_html_abs("va")
    body = f"""
<div class="wrap">
<section>
<h1>Pàgina no trobada</h1>
<p>La pàgina que busques no existix o s'ha mogut. Torna a la portada:</p>
<p><a class="boton boton-secundari boton-petit" href="/index.html">Portada en valencià</a></p>
</section>
<section>
<h1>Página no encontrada</h1>
<p>La página que buscas no existe o se ha movido. Vuelve a la portada:</p>
<p><a class="boton boton-secundari boton-petit" href="/es/index.html">Portada en castellano</a></p>
</section>
</div>
"""
    return f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta name="robots" content="noindex, nofollow">
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pàgina no trobada / Página no encontrada · AFA CEIP Alejandra Soler</title>
<link rel="icon" href="{logo}">
<link rel="stylesheet" href="{css}">
</head>
<body>

<header class="site-header">
  <div class="wrap">
    <a class="marca" href="/index.html">
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
{body}
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="avall">
      <span>{t("va", "footer_copyright")}</span>
    </div>
  </div>
</footer>

</body>
</html>
"""


# --------------------------------------------------------------------------
# robots.txt i sitemap.xml (04-09-2026, SEO)
# --------------------------------------------------------------------------

def escriure_robots():
    """PREVIEW: bloqueja tot el rastreig (Disallow: /) — mateix criteri que el
    <meta noindex> de cada pàgina. Producció: permet tot i apunta al sitemap."""
    if PREVIEW:
        contingut = "User-agent: *\nDisallow: /\n"
    else:
        contingut = f"User-agent: *\nAllow: /\nSitemap: https://{DOMINI}/sitemap.xml\n"
    write("robots.txt", contingut)


def _xml_esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generar_sitemap():
    """Sitemap XML a partir de SITEMAP_ENTRIES: EXACTAMENT les pàgines que
    render_page() ha escrit de veres i que no porten noindex (vore el
    comentari de dalt de SITEMAP_ENTRIES) — mai una llista de rutes
    inventada a banda. Cada `page_path` genera un <url> per idioma disponible,
    amb les seues bessones com <xhtml:link alternate hreflang>, igual que el
    hreflang de cada pàgina (render_page). Sense <lastmod> (no en tenim data
    fiable per pàgina). Es crida NOMÉS en producció (main() ja ho garantix)."""
    per_path = {}
    orde = []
    for lang, page_path in SITEMAP_ENTRIES:
        if page_path not in per_path:
            per_path[page_path] = set()
            orde.append(page_path)
        per_path[page_path].add(lang)

    blocs = []
    for page_path in orde:
        langs = per_path[page_path]
        abs_va = f"https://{DOMINI}/{page_path}"
        abs_es = f"https://{DOMINI}/es/{page_path}"
        alternates = []
        if "va" in langs:
            alternates.append(f'    <xhtml:link rel="alternate" hreflang="ca" href="{_xml_esc(abs_va)}"/>')
            alternates.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{_xml_esc(abs_va)}"/>')
        if "es" in langs:
            alternates.append(f'    <xhtml:link rel="alternate" hreflang="es" href="{_xml_esc(abs_es)}"/>')
        alternates_html = "\n".join(alternates)
        for lang in ("va", "es"):
            if lang not in langs:
                continue
            loc = abs_va if lang == "va" else abs_es
            blocs.append(f"  <url>\n    <loc>{_xml_esc(loc)}</loc>\n{alternates_html}\n  </url>")

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + "\n".join(blocs) + "\n</urlset>\n")
    write("sitemap.xml", xml)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    # Assets: es copien tal qual (ja viuen en el repo, no cal descarregar
    # res). NOMÉS a l'arrel de dist/ — l'arbre es/ hi arriba amb "../".
    shutil.copytree(ASSETS_SRC, os.path.join(DIST, "assets"))

    posts = load_collection("blog")
    posts.sort(key=lambda p: p["data"], reverse=True)

    activitats_totes = load_collection("extraescolars")
    activitats_actives = [a for a in activitats_totes if a.get("activa", True)]
    activitats = activitats_actives   # les municipals són fitxes normals (es_municipal: true)

    # Bilingüe (02-09-2026): l'arbre 'va' s'escriu a l'arrel de dist/ (idèntic
    # a com era abans, per defecte), l'arbre 'es' és un espill complet a
    # dist/es/ — mateixos noms de fitxer, mateixa estructura de carpetes.
    for lang in ("va", "es"):
        prefix = "" if lang == "va" else "es/"

        write(f"{prefix}index.html", pagina_home(lang))
        for slug in ("qui-som", "fes-te-de-lafa", "contacte", "mes-que-verd", "estatuts", "conciliacio"):
            write(f"{prefix}{slug}.html", pagina_estatica(slug, lang))
        write(f"{prefix}junta.html", pagina_junta(lang))
        write(f"{prefix}galeria.html", pagina_galeria(lang))

        write(f"{prefix}blog/index.html", pagina_blog_index(posts, lang))
        for p in posts:
            write(f"{prefix}blog/{p['_slug']}.html", pagina_blog_post(p, lang))

        if load_web()["extraescolars_visibles"]:
            write(f"{prefix}extraescolars/index.html", pagina_extraescolars_landing(activitats, lang))
            write(f"{prefix}extraescolars/places-lliures.html", pagina_places_lliures(lang))
            for a in activitats:
                write(f"{prefix}extraescolars/{a['_slug']}.html", pagina_activitat(a, lang))
        else:
            # Secció oculta (content/web.yml): NOMÉS s'escriu l'stub de
            # l'índex — cap fitxa ni places-lliures (vore pagina_extraescolars_stub()).
            write(f"{prefix}extraescolars/index.html", pagina_extraescolars_stub(lang))

    if not PREVIEW:
        with open(os.path.join(DIST, "CNAME"), "w", encoding="utf-8") as f:
            f.write(DOMINI + "\n")

    with open(os.path.join(DIST, ".nojekyll"), "w"):
        pass

    # SEO (04-09-2026): robots.txt sempre; 404.html sempre (útil també en
    # PREVIEW); sitemap.xml NOMÉS en producció (generar_sitemap() llig
    # SITEMAP_ENTRIES, que en PREVIEW no s'ompli — vore render_page()).
    escriure_robots()
    write("404.html", pagina_404())
    if not PREVIEW:
        generar_sitemap()

    print("Build completat a", DIST, "(PREVIEW)" if PREVIEW else "(producció)")


if __name__ == "__main__":
    main()
