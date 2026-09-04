# Web AFA CEIP Alejandra Soler — repositori editable (ADR 002)

Este repositori és la nova versió del clon de la web, transformada de "HTML pla" a
**"contingut (YAML) + generador" (build)**, per a poder connectar un editor visual
(**Pages CMS**, pagescms.org) que la junta faça servir sense veure mai HTML ni codi.
Substitueix el patró anterior (editar directament els `.html` a github.com).

Decisió completa i alternatives descartades: `docs/adr/002-editor-visual-pages-cms.md`
del repositori del projecte (`web-afa`), no d'este repositori.

## Estructura

```
content/            ← TOT el contingut editable, en YAML (esta és la part que toca la junta)
  extraescolars/     ← una fitxa .yaml per activitat (inclou "activitats-municipals.yaml")
  junta/             ← una fitxa .yaml per membre + _comissions.yaml (llista de comissions)
  blog/              ← una fitxa .yaml per entrada de notícies
  pagines/           ← 5 pàgines estàtiques (qui-som, fes-te-de-lafa, contacte, mes-que-verd, estatuts)
  places-lliures.yml ← fitxer únic (imatge del calendari mensual)
  horaris.yml        ← fitxer únic (secció "Horaris per curs" d'Extraescolars: horari
                         general, PDF de preus municipals i horari per nivell/curs)
  extraescolars-textos.yml ← fitxer únic (04-09-2026: títol, subtítol, paràgrafs
                         d'introducció, botó de places, nota dels asteriscs i
                         apartat Baixes de la LANDING d'Extraescolars)
  web.yml             ← fitxer únic (interruptor global "Extraescolars visible", 04-09-2026)
assets/              ← imatges, PDFs, CSS. Les pujades noves de l'editor van a assets/uploads/cms/
build/
  generar.py         ← el generador: llig content/+assets/ i escriu dist/
  requirements.txt   ← dependències Python (pyyaml, markdown)
.github/workflows/build.yml ← construeix i publica a GitHub Pages en cada push
.pages.yml           ← configuració de Pages CMS (quins camps veu la junta, i com)
dist/                ← NO es puja a git (.gitignore): és la web generada, la crea el workflow
```

## Com funciona (per a qui torne a este repo tècnicament)

1. La junta entra a Pages CMS (invitació per email, sense compte de GitHub) i edita
   formularis: canviar un text, activar/desactivar una extraescolar, pujar una foto...
2. Pages CMS fa un commit directe a `main` amb el canvi (només toca fitxers `.yaml` o
   puja un fitxer a `assets/uploads/cms/`).
3. Eixe push dispara `.github/workflows/build.yml`: instal·la Python, executa
   `build/generar.py`, i publica el resultat (`dist/`) a GitHub Pages amb el mètode
   oficial (`upload-pages-artifact` + `deploy-pages`).
4. En 1-2 minuts el canvi ja es veu a la web pública. La junta no fa res més.

## Build local (per a comprovar canvis abans de fer push)

```bash
cd build
pip install -r requirements.txt
python3 generar.py                # build de producció (amb CNAME, sense noindex)
PREVIEW=1 python3 generar.py      # build de preview (sense CNAME, amb noindex — el que fa CI en este repo pilot)
```

El resultat s'escriu a `dist/` (a l'arrel del repo). Obri `dist/index.html` al navegador
per a comprovar-ho.

## Per a la junta

**No cal llegir esta secció tècnica per a editar la web.** L'editor visual (Pages CMS) és
la via normal d'edició — la guia d'ús pas a pas per a la junta (com entrar, com editar
un text, com pujar una foto, com donar de baixa una extraescolar) es documenta a banda,
en un document sense codi. Demaneu-lo si no el teniu.

**Activar/desactivar una extraescolar sense l'editor** (via emergència, tècnica): a
`content/extraescolars/<activitat>.yml`, el camp `activa: true/false` decideix si
l'activitat es veu a la web (llista i fitxa pròpia) o no. No cal esborrar cap fitxer.

**Camps afegits el 28-08-2026 (curs 2026-27)**: `empresa` (qui imparteix l'activitat: davall del nom a la llista i «Impartida per:» a la fitxa), `cursos` (llista de codis I3/I4/I5 =
3/4/5 anys, P1..P6 = Primària — alimenta el desplegable «Filtrar per curs» de la landing i
la línia «Cursos» de la fitxa; buit = es veu sempre), `dossier_label`/`dossier2_label`
(text del botó quan hi ha dos dossiers, p. ex. Juegamáticas), i `form` pot quedar buit
(la fitxa mostra «Formulari d'inscripció: pendent de publicar»). Els dossiers 26-27
estan a `assets/uploads/2026/08/`. Crèdits de les portades genèriques: vore
`sitio/README.md` del projecte (§ Crèdits d'imatges).

**Ocultar una pàgina mentre la prepares (des del 04-09-2026)**: a Pàgines → obri la pàgina →
interruptor **«Visible a la web»** → posa'l en No → **Save**. La pàgina desapareix del menú i
del peu, i qui obri la seua adreça (o l'enllaç antic) veu un avís «Aquesta pàgina està en
preparació» en lloc del contingut a mitges — mai un error 404. Per a tornar-la a publicar:
el mateix interruptor en Sí.

**Si canvies `.pages.yml` i l'editor no ho reflecteix (des del 04-09-2026)**: Pages CMS guarda
la configuració en la seua base de dades i, en carregar o recarregar l'editor, NO la torna a
llegir de GitHub (verificat al codi font: `lib/config-store.ts`, el layout crida `getConfig`
sense `sync`). Només s'actualitza quan li arriba el **webhook del push** (pot tardar uns
minuts) o quan es guarda des de Settings → Configuration dins del mateix editor. Per tant:
després d'un push que toque `.pages.yml`, esperar uns minuts i recarregar; si encara no ix,
obrir Settings → Configuration i guardar (força l'actualització).

**Les 4 seccions «Extraescolars / …» del menú de Pages CMS (des del 04-09-2026)**: l'orde
del menú lateral és l'orde de declaració del bloc `content:` de `.pages.yml` (verificat al
codi font de Pages CMS, `lib/config.ts`, `normalizeContentEntries()` — cada entrada es
converteix en un ítem de navegació amb el seu `label`, en eixe mateix orde). Pages CMS SÍ
suporta grups plegables (`type: group` + `items`); s'ha preferit el prefix «Extraescolars / …»
al label perquè es vegen juntes sense haver de provar abans la configuració de grup. Les 4 seccions, en orde, i què edita cadascuna:
1. **Extraescolars / Activitats** (`extraescolars`) — les fitxes d'activitats (com sempre).
2. **Extraescolars / Places lliures** (`places-lliures`) — el calendari mensual de plaçes.
3. **Extraescolars / Horaris** (`horaris`) — NOMÉS el bloc «Horaris per curs» de la pàgina
   (imatge de l'horari general, PDF de preus municipals, horari per nivell/curs).
4. **Extraescolars / Textos de la pàgina** (`extraescolars-textos`, NOU) — la resta de textos
   fixos de la landing: títol (H1), subtítol, els 4 paràgrafs d'introducció, el text del botó
   «Vore places lliures del mes», la nota dels asteriscs (**) i l'apartat Baixes (títol +
   text). Fitxer `content/extraescolars-textos.yml`; `build/generar.py` → `load_extra_textos()`.
   Camp buit (o fitxer sencer absent) → cau al text fix original (mai la pàgina a mitges).
   Els paràgrafs (`intro1`..`intro4`, `baixes_text`) són `rich-text` (com `cos` a Pàgines):
   poden portar un `<a href="...">` (p. ex. l'enllaç a la Fundació Esportiva Municipal del
   paràgraf 2, o a Aulazon del paràgraf 4) — `cos_html()` els processa igual que qualsevol
   altre camp llarg. L'apartat Baixes es reinserix DINS d'un `<p class="nota">` fix al codi
   (no editable): si el text és un sol paràgraf (el cas normal), es lleva l'embolcall `<p>`
   que afig `cos_html()` per a no duplicar `<p class="nota"><p>...</p></p>`.

**Ocultar la secció Extraescolars sencera (des del 04-09-2026)**: **«Configuració de la
web»** → interruptor **«Secció Extraescolars visible a la web»** → No → **Save**. Desapareix
del menú, del peu i de la portada; la pàgina Extraescolars mostra només l'avís del camp
**«Avís que es mostra quan la secció està oculta»** (i la versió castellana, opcional — si es
deixa buit es mostra el text en valencià). Útil mentre es preparen les fitxes d'un curs nou:
cap fitxa antiga es veu, però tampoc cal esborrar-les.

**Enllaçar un PDF/imatge des d'un text (des del 04-09-2026)**: els camps de text llarg
(«Contingut de la pàgina», «Descripció», «Nota»...) porten `media: false` (no es pot inserir
imatges inline), però SÍ tenen el botó d'enllaç (🔗) de la barra que ix en seleccionar text —
verificat al codi font de Pages CMS (`components/ui/editor/index.tsx`): l'extensió `Link` es
carrega sempre, independentment de `media`. **Important — no hi ha cap botó "copiar ruta" a
la secció Mitjans** (verificat a `components/media/media-view.tsx` i `file-options.tsx`: el
menú ⋮ de cada fitxer només té "Rename", "Delete" i "View on GitHub"). El flux real:
1. Vés a **Mitjans** (menú lateral) → navega a la carpeta on vulgues → **Upload** → tria el
   fitxer.
2. Pages CMS li posa un nom "segur" automàticament (minúscules, sense accents ni espais —
   els espais es tornen guions; l'extensió es manté). Ex.: `Informació preus.pdf` es guarda
   com `informacio-preus.pdf`. La ruta final és sempre `/assets/uploads/cms/<eixe-nom>`.
3. Torna al camp de text, selecciona la paraula que vulgues enllaçar, clica el botó 🔗, i
   escriu a mà `/assets/uploads/cms/<nom-del-fitxer>` (seguint el patró del pas 2) → prem
   Intro o el ✓ per a aplicar.
4. Si no estàs segura del nom exacte: al fitxer de Mitjans, menú ⋮ → **View on GitHub** —
   s'obri la pàgina del fitxer a github.com; la ruta és tot el que ix després de `blob/main/`
   a l'adreça del navegador.

> ⚠️ **La ruta ha de començar per la barra `/`** (`/assets/uploads/cms/nom.pdf`). Sense la barra inicial (`assets/uploads/...`, que és com apareix a GitHub) l'editor rebutja l'enllaç **en silenci**: prems Enter o el ✓ i no passa res. És una limitació de l'editor de text (TipTap): només accepta adreces que comencen per `http(s)://`, `/`, `#` o `mailto:`. Verificat el 04-09-2026 en el codi font (regex `isAllowedUri`). Després d'enllaçar, recorda **Desar** la pàgina.

**Horaris d'extraescolars, editables des del 04-09-2026**: la secció «Horaris per curs» de
la pàgina Extraescolars (imatge de l'horari general, PDF de preus de les activitats
municipals, i una imatge d'horari per nivell/curs) ja NO és fixa al codi — es gestiona des
de Pages CMS, secció **«Horaris d'extraescolars»** (`content/horaris.yml`). Buidar un dels
dos camps individuals (Horari general / PDF de preus) fa que eixe enllaç desaparega de la
web (no torna a mostrar l'antic); si es lleva TOTA la llista d'horaris per nivell, o el
fitxer encara no s'ha tocat mai, la web mostra els valors originals de la migració
(`build/generar.py`, funció `load_horaris()`) perquè un oblit mai deixe la secció buida.

## Diferències conegudes amb el clon original (`sitio/`, `preview-github/`)

Verificat amb diff estructural (espais/salts de línia entre etiquetes normalitzats,
ver `docs/REGISTRO_TECNICO.md` del repo del projecte): **el contingut visible és
idèntic**. L'única diferència són els comentaris-guia HTML (`<!-- ══ ACTIVITAT... ══ -->`)
que hi havia al clon perquè algú sense perfil tècnic poguera esborrar blocs a mà des de
github.com — ара ja no fan falta (el camp `activa` i l'editor visual fan eixa faena),
per això el generador nou no els escriu. No afecten res del que es veu al navegador.

## Migració al repositori del AFA (quan hi haja compte del AFA)

1. Crear el repositori nou baix el compte/organització del AFA i pujar tot este contingut.
2. Reinstal·lar la GitHub App de Pages CMS sobre eixe repositori nou i tornar a convidar
   els col·laboradors (la junta) — uns 15 minuts.
3. Al workflow (`.github/workflows/build.yml`), llevar `PREVIEW: "1"` (o posar-lo a `"0"`)
   perquè es genere amb el domini propi (`CNAME`) i sense `noindex`.
4. Configurar el domini (DonDominio) apuntant a GitHub Pages — 4 registres A + CNAME `www`
   (documentació oficial de GitHub Pages).

## Límits coneguts

- Els PDF de més de 50 MB no es poden pujar des de Pages CMS (límit de l'API de GitHub)
  — caldria pujar-los per git directament. Hui el més gran és de 31,5 MB.
- El fitxer `.pages.yml` (quins camps veu la junta) el manté el perfil tècnic, no la junta.
