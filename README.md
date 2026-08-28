# Web AFA CEIP Alejandra Soler — sitio estático (Opció A)

Este és el codi de la web nova de l'AFA. **HTML + CSS + un poquet de JavaScript, sense
frameworks ni «build step»**: qualsevol fitxer `.html` es pot obrir directament al
navegador o editar-se a mà, i els canvis es veuen en publicar-se, sense compilar res.

Correspon a l'**Opció A "Clonar la web actual"** de la proposta
(`docs/propuesta/PROPUESTA_UNIFICADA_2026-08.html`): contingut migrat i ordenat, disseny
nou, cap plaça automàtica ni panell d'empreses (això és l'Opció B, fora d'esta versió).

## Com es publica (GitHub Pages)

1. Crear un repositori del **AFA** a GitHub (no personal de Jorge) — p. ex.
   `afa-alejandra-soler/web`.
2. Pujar tot el contingut d'esta carpeta (`sitio/`) a l'arrel del repositori (o a la branca
   `main`, que és el que GitHub Pages servirà).
3. Als *Settings → Pages* del repositori, activar Pages sobre la branca `main` (carpeta
   arrel `/`).
4. El fitxer `CNAME` ja porta el domini `afaalejandrasoler.es` — GitHub Pages el detecta
   sol. Falta configurar al registrador (DonDominio) els registres DNS cap a GitHub Pages
   (4 registres A + 1 CNAME per a `www`; documentació oficial de GitHub Pages).
5. El fitxer `.nojekyll` evita que GitHub intente processar el lloc amb Jekyll (no en fa
   falta cap, són fitxers estàtics tal qual).
6. HTTPS: GitHub Pages l'activa sol en quant el DNS estiga verificat (casella "Enforce
   HTTPS" als Settings → Pages).

## Com editar contingut (per a algú sense perfil tècnic)

**El lloc s'edita tocant directament el fitxer HTML de cada pàgina** — no cal executar cap
script ni "compilar" res. Cada pàgina és un fitxer `.html` independent amb un nom clar
(`contacte.html`, `qui-som.html`...). Per canviar un text, obrir el fitxer amb un editor
(fins i tot el mateix GitHub, botó del llapis ✏️) i editar directament dins del text — la
part de dalt (`<head>`, el menú, el peu) NO cal tocar-la.

- Les fitxes d'extraescolars viuen a `extraescolars/` (una pàgina per activitat).
- Per pujar un PDF/imatge nou (dossier, calendari de places), cal penjar-lo a la carpeta
  `assets/uploads/` (mantenint la mateixa subcarpeta per any/mes és opcional, però ajuda a
  no barrejar-ho tot) i canviar l'enllaç de la pàgina corresponent.
- **`scripts/2026-08-26_generar_sitio_clon.py` és una eina de bootstrap, no un pas
  obligatori**: es va fer servir UNA VEGADA per generar les ~30 pàgines inicials a partir
  d'una plantilla comuna (evitar copiar/pegar la capçalera i el peu a mà). Si en el futur cal
  regenerar contingut massivament (p. ex. afegir moltes fitxes noves de colp), es pot tornar
  a executar — però el dia a dia és editar l'HTML.
- **Editor visual senzill**: pendent de valorar (l'opció A promet "un editor de contingut
  molt senzill" — vore `docs/PENDIENTES.md`). De moment, l'edició és directament el fitxer
  HTML des de GitHub.

## Com llevar o afegir una extraescolar (guia sense coneixements tècnics)

Cada extraescolar apareix en DOS llocs: la seua pròpia pàgina dins de `extraescolars/`
(per exemple `judo.html`) i la seua "tarjeta" (foto + nom) dins de
`extraescolars/index.html`. Per a fer-ho fàcil sense saber HTML, dins del codi de cada
fitxer hi ha comentaris de guia que marquen exactament on comença i on acaba cada bloc
— es busquen amb Ctrl+F / Cmd+F pel nom de l'activitat, tal com s'explica ací baix.

**Per a LLEVAR una extraescolar** (per exemple, si una empresa deixa de vindre):

1. Entra a github.com, obri el repositori de la web i entra a la carpeta `extraescolars`.
2. Obri el fitxer de l'activitat (per exemple `judo.html`) i esborra'l sencer (icona de
   la paperera 🗑️ a dalt a la dreta del fitxer) — a baix, "Commit changes" per a guardar.
3. Obri ara `extraescolars/index.html` amb el llapis ✏️ (editar).
4. Busca (Ctrl+F) el text `ACTIVITAT: Judo` (canvia "Judo" pel nom real). Trobaràs una
   línia que diu `<!-- ══ ACTIVITAT: Judo ... ══ -->` i, unes línies més avall, una altra
   que diu `<!-- ══ FI ACTIVITAT: Judo ══ -->`.
5. Selecciona i esborra TOT el que hi ha entre eixes dos línies (incloent-les totes dos) i
   guarda els canvis ("Commit changes"). L'activitat ja no eixirà en la llista.

**Per a AFEGIR una extraescolar nova:**

1. Dins de `extraescolars/`, obri l'activitat existent que més s'assemble a la nova.
2. Fes-ne una còpia amb un nom nou (per exemple, descarrega el fitxer, canvia-li el nom a
   `karate.html` i torna'l a pujar a la mateixa carpeta).
3. Obri la còpia i canvia únicament el text: nom de l'activitat, descripció, enllaç al
   dossier i al formulari d'inscripció (no cal tocar res més del fitxer).
4. Obri `extraescolars/index.html`, busca el bloc `<!-- ══ ACTIVITAT: ... ══ -->` d'una
   activitat pareguda, copia'l sencer (des d'eixa línia fins «FI ACTIVITAT») i enganxa'l
   just davall.
5. Dins del bloc enganxat, canvia el nom de l'activitat i l'enllaç (`href="karate.html"`)
   perquè apunte a la pàgina nova, i guarda els canvis.

Si no et veus amb cor de tocar-ho directament, envia el canvi (nom de l'activitat + què
cal fer) a qui porte la web en eixe moment — els passos d'ací dalt són precisament perquè
qualsevol puga fer-ho sense conéixer HTML.

## Estructura de carpetes

```
sitio/
├── index.html                     Home
├── qui-som.html, fes-te-de-lafa.html, contacte.html,
│   junta.html, estatuts.html, mes-que-verd.html   Pàgines estàtiques migrades
├── es/index.html                  Versió en castellà — "properament" (fase següent)
├── extraescolars/
│   ├── index.html                 Landing amb graella de totes les activitats vigents
│   ├── places-lliures.html        Calendari mensual de places (manual, com sempre)
│   ├── activitats-municipals.html Grup d'activitats de la FDM (Bàsquet, Escacs, etc.)
│   └── <activitat>.html           Una pàgina per activitat (dossier + inscripció)
├── assets/
│   ├── css/style.css              Full d'estils compartit (únic per a tot el lloc)
│   ├── img/logo-afa.png           Logo de l'AFA
│   └── uploads/                   PDF/imatges propis (dossiers, fotos junta, estatuts...)
├── CNAME                          Domini (afaalejandrasoler.es)
├── .nojekyll                      Desactiva el processament Jekyll de GitHub
└── ASSETS_PENDIENTES.tsv          Històric — resolt el 26-08-2026, ja no queda cap fitxer
                                    pendent de descàrrega (veure més avall)
```

## Assets locals (`ASSETS_PENDIENTES.tsv` — resolt)

Tots els dossiers en PDF i les imatges de calendari es van descarregar el 26-08-2026
(script `scripts/2026-08-26_descargar_uploads.py`, 358,5 MB) i ja estan copiats a
`sitio/assets/uploads/`, amb la mateixa subcarpeta any/mes que tenien a
`wp-content/uploads/` de la web anterior. El fitxer `ASSETS_PENDIENTES.tsv` es manté buit
(només capçalera) com a registre històric — no cal tocar-lo.

**Curs 2026-27 (28-08-2026)**: els dossiers nous de cada empresa estan a
`assets/uploads/2026/08/<activitat>-2026-27.pdf` (comprimits per a web; els originals, fora
del repositori, a `material/dossiers-2026-27/` del projecte). Ja no hi ha cap dossier a Google
Drive: tots són locals. Els formularis són els del PDF «Formularis inscripció 26-27» del AFA.

## Desplegable «Mostrar» de la pàgina d'extraescolars

Cada tarjeta porta els cursos de l'activitat (`data-cursos="I4 I5 P1 ..."`, llegits del
dossier). El desplegable filtra i reordena al navegador, sense servidor. Si una activitat no
declara cursos (`data-cursos="*"`) es veu sempre. Per a canviar els cursos d'una activitat sense
l'editor: modifica eixe atribut a la tarjeta d'`extraescolars/index.html` i la línia «Cursos:»
de la seua fitxa.

## Crèdits d'imatges (portades d'extraescolars)

Les portades ixen del dossier de cada activitat, excepte estes, d'ús lliure (obligació
d'atribució per a les CC BY):

- Acting in English — «Assortment of theatre masks», virtusincertus (Flickr), CC BY 2.0
- Cor (Acting in English) — «Chorus sheet music», David Beale (Unsplash/Wikimedia Commons), CC0
- Breaking — «Le breakdance», Daniel Wehner (Flickr), CC BY 2.0
- ExpresArte — «Prints», bfick (Flickr), CC BY 2.0
- CreActivitat — «Labyrinthine circuit board lines», quapan (Flickr/Wikimedia Commons), CC BY 2.0
- Anglès (Acting in English) — composició tipogràfica pròpia

## Què NO inclou esta versió (és Opció B, fora d'abast)

- Plaças que s'actualitzen soles (panell d'empreses) — el calendari de
  `extraescolars/places-lliures.html` es continua pujant a mà.
- Calendari interactiu ni PDF generat automàticament.
- Estadístiques de plaçes ni Drive per extraescolar.

## Pendents de contingut

Este lloc és un **clon fiel** de la web anterior (política del 26-08-2026: es copia tal
com és, sense depurar RGPD ni inventar contingut). Les inconsistències detectades durant
el clon (fotos duplicades, dossiers compartits entre activitats, etc.) NO es mostren com
a avisos a la web — estan documentades a `docs/INFORME_INCONSISTENCIAS_2026-08-26.md`.
Pendent real per al AFA: revisar RGPD abans de publicar en domini públic (llista a
`docs/PENDIENTES.md`, P1), i decidir si es vol una pàgina d'avís legal/privacitat (la web
anterior no en tenia cap).
