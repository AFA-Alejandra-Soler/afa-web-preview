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
  places-lliures.yaml ← fitxer únic (imatge del calendari mensual)
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
