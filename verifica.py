#!/usr/bin/env python3
"""Cancello di qualità: niente arriva sul telefono se questo script non passa.

Gira sia in locale (`python verifica.py`) sia in CI su ogni pull request e su
ogni push. Se fallisce, GitHub Pages NON pubblica e il telefono continua a
servire l'ultima versione buona.

Il controllo più importante non è tecnico: è che la copia in `stabile/` non
venga mai toccata. È la rete di sicurezza di chi sta viaggiando.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile

RADICE = pathlib.Path(__file__).parent
errori: list[str] = []
avvisi: list[str] = []


def err(m): errori.append(m)
def avv(m): avvisi.append(m)


# --- 1. la copia congelata non si tocca ------------------------------------
def impronta(percorso: pathlib.Path) -> str:
    """SHA256 con i fine riga normalizzati.

    Git converte LF↔CRLF a seconda del sistema: senza normalizzare, lo stesso
    file darebbe hash diversi su Windows e sulla CI Linux, e il controllo
    fallirebbe per un motivo che non c'entra niente col contenuto.
    """
    return hashlib.sha256(percorso.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


stab = RADICE / "stabile" / "index.html"
sha_file = RADICE / "stabile" / "SHA256"
if not stab.exists() or not sha_file.exists():
    err("stabile/: la copia di emergenza è sparita. Va ripristinata prima di procedere.")
else:
    atteso = sha_file.read_text(encoding="utf-8").strip()
    trovato = impronta(stab)
    if atteso != trovato:
        err(f"stabile/index.html è stato modificato.\n"
            f"   atteso  {atteso}\n   trovato {trovato}\n"
            f"   È la copia che salva il viaggiatore quando tutto il resto si rompe: non va toccata.")

# --- 2. sorgente e copia pubblicata allineate ------------------------------
src = RADICE / "copenaghen-2026.html"
idx = RADICE / "index.html"
if not src.exists():
    err("manca copenaghen-2026.html (la sorgente)")
elif not idx.exists():
    err("manca index.html — lancia `python build.py`")
elif src.read_bytes().replace(b"\r\n", b"\n") != idx.read_bytes().replace(b"\r\n", b"\n"):
    err("index.html non corrisponde alla sorgente — lancia `python build.py` e ricommitta")

testo = idx.read_text(encoding="utf-8") if idx.exists() else ""

# --- 3. il JavaScript deve almeno compilare --------------------------------
m = re.search(r"<script>(.*)</script>", testo, re.S)
if not m:
    err("nessun blocco <script> in index.html")
else:
    js = m.group(1)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js)
        tmp = f.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        err("il JavaScript non compila:\n   " + (r.stderr or "").strip().replace("\n", "\n   "))

    # --- 4. i dati dell'itinerario reggono ---------------------------------
    prova = re.split(r"/\* -+ app -+ \*/", js)[0]
    for fn in ("renderOggi", "renderGiorni", "renderBiglietti", "renderCibo", "renderSOS"):
        prova = re.sub(r"function " + fn + r"\(\)\{.*?\n\}\n", "", prova, flags=re.S)
    prova += """
const out = { giorni: DAYS.length, tappe: 0, ordine: [], vuoti: [], badge: {} };
for (const d of DAYS) {
  if (!d.stops || !d.stops.length) out.vuoti.push(d.id);
  out.tappe += (d.stops||[]).length;
  let prec = -1;
  for (const s of d.stops || []) {
    const [H, Mi] = String(s.t).split(":").map(Number);
    if (Number.isNaN(H) || Number.isNaN(Mi)) { out.ordine.push(d.id + " ora illeggibile: " + s.t); continue; }
    const v = H * 60 + Mi;
    if (v < prec) out.ordine.push(d.id + " fuori ordine a " + s.t);
    prec = v;
    if (s.badge) out.badge[s.badge[0]] = (out.badge[s.badge[0]] || 0) + 1;
  }
  if (!d.food || !d.food.items || !d.food.items.length) out.vuoti.push(d.id + " senza cibo");
  if (typeof dayHTML(d, false) !== "string" || dayHTML(d, false).length < 400) out.vuoti.push(d.id + " render vuoto");
}
console.log(JSON.stringify(out));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(prova)
        tmp2 = f.name
    r2 = subprocess.run(["node", tmp2], capture_output=True, text=True)
    if r2.returncode != 0:
        err("i dati dell'itinerario non si caricano:\n   " + (r2.stderr or "").strip().split("\n")[0])
    else:
        d = json.loads(r2.stdout.strip().splitlines()[-1])
        if d["giorni"] != 6:
            err(f"servono 6 giornate, ne trovo {d['giorni']}")
        if d["tappe"] < 80:
            err(f"solo {d['tappe']} tappe: sospetto che ne siano state perse (attese ~90)")
        for x in d["ordine"]:
            err("orari non crescenti → " + x)
        for x in d["vuoti"]:
            err("giornata incompleta → " + x)
        print(f"   itinerario: {d['giorni']} giorni, {d['tappe']} tappe, bollini {d['badge']}")

# --- 5. gli agganci dell'interfaccia devono esistere ------------------------
for elemento, perche in [
    ('id="p-oggi"', "scheda Oggi"), ('id="p-giorni"', "scheda Giorni"),
    ('id="p-biglietti"', "scheda Biglietti"), ('id="p-cibo"', "scheda Cibo"),
    ('id="p-parlare"', "scheda Parlare"), ('id="p-sos"', "scheda SOS"),
    ('id="updbar"', "barra di aggiornamento"),
    ('id="addrView"', "riquadro dell'indirizzo"), ("schermataEmergenza", "schermata di emergenza"),
    ('href="./stabile/"', "via d'uscita verso la copia bloccata"),
]:
    if elemento not in testo:
        err(f"manca {perche} ({elemento})")

# --- 6. nessun dato personale nel repo pubblico ----------------------------
personali = [
    (r"[A-Za-zÆØÅæøå]+vej \d{1,3}(?!.*(Kongevej|Gl\.))", "un indirizzo danese"),
    (r"\b\d{4} Kastrup\b", "il CAP di casa"),
    (r"\+45[ ]?\d{8}", "un numero di telefono danese"),
    (r"\b[A-Z]{2}\d{3,4}\b(?=.*(volo|Fiumicino|Roma))", "un numero di volo"),
]
for f in RADICE.rglob("*"):
    if not f.is_file() or ".git" in f.parts or f.suffix not in (".html", ".md", ".js", ".json", ".py", ".yml"):
        continue
    if f.name == "verifica.py":
        continue
    t = f.read_text(encoding="utf-8", errors="ignore")
    for pat, cosa in personali:
        for hit in re.finditer(pat, t):
            if "Kongevej" in hit.group(0):
                continue
            err(f"{f.relative_to(RADICE)}: sembra esserci {cosa} → «{hit.group(0)}». "
                f"Questo repo è pubblico: i dati di casa si inseriscono nell'app, non nel codice.")

# --- 7. il service worker deve restare prudente ----------------------------
sw = RADICE / "sw.js"
if sw.exists():
    s = sw.read_text(encoding="utf-8")
    # via i commenti, altrimenti una riga che *nomina* skipWaiting sembra una chiamata
    scodice = re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", s, flags=re.S))
    if 'addEventListener("install"' in scodice:
        blocco = scodice.split('addEventListener("install"')[1].split("addEventListener")[0]
        if re.search(r"skipWaiting\s*\(", blocco):
            err("sw.js: skipWaiting dentro l'install fa aggiornare l'app di nascosto. "
                "Deve aspettare che sia l'utente a toccare la barra.")
    if "oresund-v" not in s:
        avv("sw.js: non trovo il nome della cache versionata")

# --- esito ------------------------------------------------------------------
print()
for a in avvisi:
    print("  ⚠  " + a)
if errori:
    print("  ✗ VERIFICA FALLITA — non si pubblica\n")
    for e in errori:
        print("   • " + e)
    sys.exit(1)
print("  ✓ verifica superata: si può pubblicare")
