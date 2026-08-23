# Sei Giorni sull'Øresund — istruzioni per chi lavora su questo repo

App di viaggio per **Copenaghen, Malmö e Lund, 24–29 agosto 2026**. Chi la usa è un viaggiatore
italiano che **non parla inglese**, non è un viaggiatore esperto, ha un budget stretto e vuole
poter contare su quello che legge. Sua sorella lo raggiunge giovedì 27 sera e riparte con lui
sabato 29.

---

## ⛔ Le tre regole che vengono prima di tutto

**1 · Proponi, non decidere.**
Non modificare mai il piano di tua iniziativa. Se scopri che piove, che un posto ha chiuso, che un
treno è soppresso: **scrivi cosa proponi e perché, e fermati lì.** La decisione è sua, sempre, anche
quando la tua proposta è ovviamente giusta. Puoi preparare la modifica in una pull request, così
lui vede esattamente cosa cambierebbe — ma **non unire mai niente da solo**, e non esiste nessun
auto-merge in questo repo. Se ti viene la tentazione di «sistemare al volo» qualcosa perché tanto è
banale: quella è esattamente la cosa che non deve succedere.

**2 · Nessun dato personale nel repo.**
L'indirizzo di casa, il telefono dell'host, i numeri di volo, i dati della carta: **non entrano nel
codice.** Il repo è pubblico. Quei dati li scrive lui dentro l'app (scheda SOS → «modifica») e
restano nel `localStorage` del suo telefono. Se ti chiede di metterli nel file, ricordagli che il
repo è pubblico e proponi il campo nell'app.

**2-bis · Non puoi rompere l'app, e non devi provarci.**
Chi la usa è in viaggio: se l'app si rompe, perde l'itinerario mentre è dall'altra parte d'Europa.
Ci sono quattro strati, e **nessuno dei quattro va indebolito o aggirato**:

- **`stabile/`** è la copia congelata prima della partenza. Non registra il service worker, non ha
  manifest, non cambia mai. **Non modificarla, per nessun motivo.** `verifica.py` controlla il suo
  SHA256 e la CI rifiuta ogni proposta che la tocchi.
- **`verifica.py`** è il cancello: sintassi, 6 giornate, ~90 tappe, orari in ordine crescente,
  elementi dell'interfaccia presenti, nessun dato personale. **Lancialo prima di proporre qualsiasi
  cosa.** In CI gira da solo, e se fallisce **GitHub Pages non pubblica**: il telefono continua a
  servire l'ultima versione buona.
- **La schermata di emergenza** nell'app: se il render lancia un'eccezione, l'utente vede comunque
  l'indirizzo di casa, i numeri utili e due vie d'uscita. Non toccare `schermataEmergenza()` né il
  `try/catch` che la invoca.
- **Il service worker non si aggiorna di nascosto.** Niente `skipWaiting()` nell'install: la versione
  nuova aspetta che sia l'utente a toccare la barra. Se metti `skipWaiting` lì, `verifica.py` fallisce.

**3 · Se cambi un fatto, cambia il bollino.**
Ogni voce porta il suo grado di certezza. Non spostarne mai uno verso il verde senza aver
davvero aperto la fonte ufficiale. È l'unica cosa che rende questa app affidabile.

| Bollino | Significato |
|---|---|
| `["ok","testo"]` | 🟢 verificato su fonte ufficiale, con `src:` che linka la pagina |
| `["warn","testo"]` | 🟡 stagionale, «fino a esaurimento», meteo-dipendente: da ricontrollare sul posto |
| `["risk","testo"]` | 🔴 non confermato |

---

## Com'è fatta

Una pagina sola, autoportante. Nessuna dipendenza esterna a parte i font di Google.

```
copenaghen-2026.html   LA SORGENTE — si modifica questa
index.html             copia generata: NON modificarla a mano
build.py               copia la sorgente in index.html
manifest.webmanifest   nome, icone, schermo intero (PWA)
sw.js                  funzionamento offline + avviso di aggiornamento
icon-*.png             icone generate
```

**Dopo ogni modifica: `python build.py`.** Se non lo fai, l'app pubblicata resta indietro.

I contenuti stanno tutti nell'array `DAYS` in cima allo `<script>`. Una tappa è:

```js
{ t:"12:40",              // ora — devono restare in ordine crescente nella giornata
  h:"Titolo",             // titolo
  v:9,                    // voto 1–10 (opzionale)
  key:1,                  // tappa importante: pallino colorato sul binario
  b:"…", b2:"…",          // corpo, uno o due paragrafi
  hop:"…",                // riquadro del tragitto: partenza → linea → direzione → scendi a X
  warn:"…",               // riga rossa di avvertimento
  price:"70 DKK",
  badge:["ok","testo"],   // vedi regola 3
  src:"https://…",        // la fonte ufficiale
  map:"query per Google Maps" }
```

Ogni giornata ha anche un blocco `food` con «dove mangi oggi».

Il render è in fondo (`stopHTML`, `dayHTML`, `foodHTML`, `renderOggi`…). La scheda **Oggi** risolve
da sola la data e apre la giornata giusta; prima della partenza mostra la lista delle cose da fare.

### Lavorare senza sprecare contesto

`copenaghen-2026.html` è un file solo da ~90 KB (~25.000 token). Leggerlo tutto per cambiare un
orario è uno spreco, e su una sessione lunga diventa un problema. Quindi:

- **Non aprire mai il file intero.** Trova prima la riga: `grep -n '"10:36"' copenaghen-2026.html`
  oppure `grep -n 'id:"ven"' copenaghen-2026.html`, poi leggi solo quelle righe.
- **Le giornate hanno un id**: `lun mar mer gio ven sab`. Per saltare a una: `grep -n 'id:"gio"'`.
- **Modifica con Edit mirati**, non riscrivendo blocchi grandi.
- **Una sessione per richiesta.** Non tenerne una aperta per giorni: ogni sessione cloud riparte
  pulita clonando il repo, ed è esattamente quello che vuoi.
- `verifica.py` ti dice in due secondi se hai rotto qualcosa: costa molto meno che rileggere.

### Controllo prima di consegnare

```bash
python build.py
node --check <(python -c "import re;print(re.search(r'<script>(.*)</script>',open('index.html',encoding='utf-8').read(),re.S).group(1))")
grep -nEi "vej [0-9]{1,3}|[0-9]{4} kastrup|\+45 ?[0-9]{8}" index.html   # dev'essere vuoto
```
E verifica che gli orari di ogni giornata restino **in ordine crescente**.

---

## Il viaggiatore, in breve

- **Sveglia alle 9**, sempre. È un vincolo, non una preferenza: gli orari sono calcolati su quello.
- **Appartamento con cucina, preso apposta per risparmiare.** Colazioni e cene a casa, pranzi da
  asporto mangiati camminando o al parco. **Niente ristoranti**: banco, carretto, forno, sacco.
- **Non parla inglese.** Ogni istruzione va scritta come se dovesse eseguirla senza chiedere niente
  a nessuno. I tragitti nel formato `partenza → linea → direzione (capolinea) → scendi a NOME`, e il
  documento dice esplicitamente di **non contare le fermate** ma di leggere il nome sul display.
- **Base a Kastrup**, metro M2, prima fermata dall'aeroporto.

## Biglietti — la parte più delicata

- **Danimarca: carta.** City Pass alle macchinette. Il conteggio parte dall'acquisto, non
  dall'attivazione.
- **Svezia: app Skånetrafiken.** `Select stops` → tre fermate (CPH Airport Kastrup, Lund C, Malmö C)
  → deve comparire **Öresundszon** → `24 hours` → **360,00 kr**. Le altre due voci del selettore
  (`city zone`, `entire Scania`) **non coprono il ponte**.
- **Multa in Svezia: 1.500 SEK**, e a bordo non si vendono biglietti.
- Serve **carta d'identità o passaporto**: la patente non vale, e la polizia controlla a Hyllie.

## Cose già verificate — non rifarle, e non contraddirle senza fonte

Verifica del **21 agosto 2026** su fonti ufficiali. Le correzioni trovate allora:

- **Marmorkirken chiude alle 17** (lun–gio): è stata tolta dal lunedì, dove il piano la metteva alle 17:15.
- **Bus 35 il sabato: ai minuti :06 e :36, 18 minuti di viaggio.** Il bus delle 10:25 non esiste.
- **Glyptotek e Thorvaldsens sono gratis solo l'ULTIMO mercoledì del mese** (regola comunale dal
  1º luglio 2024). Il 26 agosto 2026 lo è — per coincidenza, non per regola.
- ~~Il biglietto del Glyptotek va prenotato~~ — **era sbagliato, corretto il 23 agosto 2026.**
  Il biglietto da 0 corone **non esiste**: lo shop ufficiale (`billet.glyptoteket.dk`) vende solo
  adulto 135, u27 108 e gruppi 121,50, **senza selettore di data né fascia oraria**, e su ogni voce
  c'è scritto «NB: Free entry on the last Wednesday of every month». Mercoledì si entra e basta.
  Non rimetterlo: chi lo legge rischia di comprare un biglietto a pagamento in un giorno gratis.
- Prezzi corretti: Glyptotek **150** (non 120), M/S Søfart **145** (non 130), Juno **30** (non 45–55).
- **Torre di Christiansborg: mar–sab 11–21**, gratis, senza prenotazione. Un aggregatore diceva
  «lun–ven 10–17» ed era falso: ha vinto il sito del Folketinget.
- **Christiania:** Pusher Street smantellata dagli abitanti nell'aprile 2024, oggi **si fotografa**.

### Ricontrollo del 23 agosto 2026, alla vigilia della partenza

- **Glyptotek: parte del museo è chiusa.** «From week 16 until October 2026, we are rearranging the
  museum's collection of Greek and Roman Sculpture and the Central Hall» → «some artworks or objects
  are temporarily unavailable, and certain galleries are closed». Mercoledì 10–17 confermato.
- **Kronborg:** 150 in cassa, **135 online**, valido 1 anno, nessuna data da scegliere. Ago: lun–dom 10–18.
- **Guglia di Vor Frelsers:** 70 DKK **uguali online e allo sportello** — prenotare non fa risparmiare,
  serve solo a saltare la fila. Tutti i giorni 9–20, ultimo ingresso 19:30, chiude con pioggia o vento forte.
- **Fredagsrock venerdì 28: TV-2 alle 22:00**, confermato, più un support act alle 19:00.
- **Smørrebrødets Dag sabato 29: 11:00–15:00**, Festivalpladsen, Flæsketorvet 45, ingresso gratuito.
- **IVA sul cibo — è una differenza di prezzo, non una formalità.** Danimarca: 25% piatta, mangiato lì
  o da asporto è uguale. **Svezia: dal 1º aprile 2026 l'asporto è al 6%, il servizio al tavolo al 12%**
  (riduzione temporanea fino al 31 dicembre 2027, fonte Skatteverket). In Svezia te lo chiederanno
  sempre, perché sono obbligati a battere due aliquote. Sta nella scheda Cibo, blocco «Al banco».
- **Kystbanen:** nessun lavoro annunciato per la settimana 24–29 agosto, ma **non confermabile da
  remoto** — l'API 1.0 di Rejseplanen è chiusa. Va guardato su Rejseplanen la mattina stessa.
- **Il check-in dell'Airbnb è alle 15:00**, non alle 13:50 come diceva il piano. Lunedì è stato
  riscritto: atterraggio 12:55 → City Pass → Kastrup 13:35 → mangiare 13:45 → **Kastrup Søbad**
  14:05 → check-in 15:00 → spesa 15:20 → centro 16:00. **Non rimettere il check-in prima delle 15.**
- **Il gate sugli indirizzi blocca anche i locali pubblici.** La regex `...vej <numero>` non sa
  distinguere casa da un negozio: scrivi la via **senza civico** e lascia il resto al campo `map:`.
  Non allargare la regex per farci passare un indirizzo.

### La scheda «Parlare»

Sesta scheda, `id="p-parlare"`, render in `renderParlare()`. Contiene gli scambi che il viaggiatore
si aspetta di sentire — trasporti, musei, banchi, imprevisti — nel formato **ti dicono / vuol dire /
rispondi**, piu' otto parole danesi con la pronuncia approssimata.

- **Il contenuto e' tutto 🟡 e lo dichiara in fondo**: nessuna fonte ufficiale certifica come parla
  un commesso. Non promuoverlo a verde.
- **In inglese, non in danese.** In Danimarca e Svezia l'inglese lo sanno tutti: le frasi da dare
  sono inglesi e corte. Il danese serve solo a *riconoscere* cosa ti stanno chiedendo.
- La barra delle schede e' `grid-template-columns:repeat(6,1fr)`. **Se ne aggiungi una settima**,
  le etichette non ci stanno piu' a 320px: misura prima di aggiungere.
- `verifica.py` controlla che la scheda esista.

⚠️ **Domini che non rispondono a WebFetch** (403, 404 o pagine JavaScript vuote): `skanetrafiken.se`,
`ft.dk`, `cph.dk`, `timeanddate.com`. Vanno letti con un browser.

## Le voci 🟡 da ricontrollare in loco

Sono marcate gialle **apposta**, non per pigrizia: nessuno può garantirle da remoto.
Gasoline Grill (chiude a esaurimento) · Grundtvigs (funerali non annunciabili in anticipo) ·
la guglia di Vor Frelsers (chiude con vento o pioggia) · Reffen e Lille Bakery (stagionali) ·
i supermercati di Kastrup · il prezzo del City Pass 48 ore.

## Decisioni da non ribaltare senza parlarne

Sono in **`docs/decisioni.md`**, con la motivazione di ciascuna. Il diario completo resta sulla
macchina locale e non è in questo repo apposta: conteneva l'indirizzo di casa. Le più vincolanti:

- **D-010** — l'app è l'unica consegna (PDF, artifact e Notion sono in pensione)
- **D-011** — ogni fatto porta il suo grado di certezza; non si promette il 100%
- **D-004** — biglietto svedese verso **Lund**, non Malmö: Malmö è fermata intermedia
- **D-003** — carta in Danimarca, app in Svezia
- **D-009** — la sveglia alle 9 è un vincolo di progetto
