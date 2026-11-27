#!/usr/bin/env python3
"""
pubblica_pagine.py
Trasforma l'export CSV di Google Moduli in un piccolo sito statico:
una pagina .html per ogni risposta + un index.html con l'elenco da cui
i ragazzi ritrovano la loro pagina.

Uso:
    python3 pubblica_pagine.py risposte.csv
    python3 pubblica_pagine.py risposte.csv --immagini immagini
    python3 pubblica_pagine.py risposte.csv --escludi pippo-x marco

Il CSV deve avere (dopo l'eventuale colonna "Informazioni cronologiche"
che Google aggiunge da solo) prima il NOME e poi il CODICE della pagina.
Se le colonne sono diverse, indica le intestazioni con --col-nome e
--col-codice.

Il sito viene scritto nella cartella "sito" (modificabile con --uscita).
Rilanciare lo script rigenera tutto: l'ultima versione inviata da un
ragazzo con lo stesso nome sostituisce la precedente.

Solo libreria standard di Python 3.8+: nessuna installazione.
"""

import argparse
import csv
import html
import re
import shutil
import sys
import unicodedata
from pathlib import Path

NOMI_RISERVATI = {"index", "immagini"}
MAX_CARATTERI = 200_000
MAX_NOME_FILE = 30

# Politica di sicurezza inserita in ogni pagina: gli script e gli stili
# scritti nella pagina funzionano, ma la pagina non può caricare nulla da
# altri siti (script esterni, immagini remote, frame, richieste di rete).
# È un aiuto in più: la protezione vera si imposta sul server (vedi README
# del consiglio) e con la revisione delle segnalazioni qui sotto.
CSP = (
    "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; "
    "script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"
)
META_SICUREZZA = (
    f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
    '<meta name="robots" content="noindex, nofollow">\n'
)

# Cose che meritano un'occhiata prima di pubblicare.
SOSPETTI = [
    (r"<script[^>]+src\s*=", "carica uno script da un altro sito"),
    (r"<iframe", "contiene un iframe"),
    (r"<(object|embed)", "contiene un oggetto incorporato"),
    (r"<form", "contiene un modulo"),
    (r"<meta[^>]+http-equiv\s*=\s*[\"']?refresh", "reindirizza ad un'altra pagina"),
    (r"\blocation\s*[.=]", "usa 'location' (possibile reindirizzamento)"),
    (r"document\.cookie|localStorage|sessionStorage|fetch\s*\(|XMLHttpRequest",
     "usa cookie, memoria del browser o rete"),
    (r"https?://", "contiene un indirizzo web"),
]


def crea_nome_file(testo):
    """Nome libero -> nome di file sicuro: minuscolo, senza accenti né spazi."""
    t = unicodedata.normalize("NFKD", testo)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return t[:MAX_NOME_FILE].strip("-")


def pulisci_testo(testo):
    """Toglie i caratteri di controllo e gli spazi in eccesso."""
    t = "".join(c for c in testo if c.isprintable() or c == " ")
    return " ".join(t.split())


def inietta_sicurezza(codice):
    """Inserisce charset, CSP e noindex all'inizio dell'head."""
    extra = META_SICUREZZA
    if not re.search(r"<meta[^>]+charset", codice, re.I):
        extra = '<meta charset="UTF-8">\n' + extra
    m = re.search(r"<head[^>]*>", codice, re.I)
    if m:
        return codice[:m.end()] + "\n" + extra + codice[m.end():]
    m = re.search(r"<html[^>]*>", codice, re.I)
    if m:
        return (codice[:m.end()] + "\n<head>\n" + extra + "</head>\n"
                + codice[m.end():])
    # frammento senza struttura: lo avvolgiamo in una pagina completa
    return ("<!DOCTYPE html>\n<html lang=\"it\">\n<head>\n" + extra
            + "<title>Pagina</title>\n</head>\n<body>\n" + codice
            + "\n</body>\n</html>\n")


def segnalazioni(codice):
    trovate = []
    for modello, descrizione in SOSPETTI:
        if re.search(modello, codice, re.I):
            trovate.append(descrizione)
    return trovate


def trova_colonne(intestazioni, col_nome, col_codice):
    def cerca(titolo):
        for i, h in enumerate(intestazioni):
            if h.strip().lower() == titolo.strip().lower():
                return i
        sys.exit(f"Colonna '{titolo}' non trovata. Intestazioni presenti: "
                 + " | ".join(intestazioni))

    if col_nome and col_codice:
        return cerca(col_nome), cerca(col_codice)
    inizio = 0
    primo = intestazioni[0].lower() if intestazioni else ""
    if "cronologic" in primo or "timestamp" in primo:
        inizio = 1
    if len(intestazioni) < inizio + 2:
        sys.exit("Servono almeno due colonne: nome e codice della pagina.")
    return (cerca(col_nome) if col_nome else inizio,
            cerca(col_codice) if col_codice else inizio + 1)


PAGINA_INDICE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
{sicurezza}<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Orientamento 2026 - IIS Marconi</title>
<style>
  body {{ font-family: Verdana, sans-serif; max-width: 640px; margin: 0 auto;
         padding: 24px; background: #fff4e0; color: #333; line-height: 1.6; }}
  header {{ display: flex; align-items: center; gap: 18px; margin-bottom: 8px; }}
  .logo {{ width: 96px; height: 96px; flex: none; object-fit: contain;
          border-radius: 12px; }}
  .logo-vuoto {{ border: 2px dashed #d84315; opacity: 0.35; box-sizing: border-box; }}
  .occhiello {{ margin: 0; color: #d84315; font-weight: bold; letter-spacing: 1px;
               text-transform: uppercase; font-size: 0.85em; }}
  .sotto {{ margin: 4px 0 0; color: #666; font-size: 0.95em; }}
  h1 {{ color: #d84315; margin: 2px 0 0; line-height: 1.2; }}
  input {{ width: 100%; box-sizing: border-box; font-size: 1.1em; padding: 10px;
          border: 2px solid #d84315; border-radius: 8px; margin-bottom: 16px; }}
  ul {{ list-style: none; padding: 0; }}
  li a {{ display: block; padding: 10px 14px; margin: 6px 0; background: white;
         border-radius: 8px; color: #d84315; text-decoration: none;
         font-size: 1.1em; }}
  li a:hover {{ background: #ffe0b2; }}
</style>
</head>
<body>
<header>
{logo}
<div>
<p class="occhiello">Orientamento 2026</p>
<h1>Le nostre prime pagine web</h1>
<p class="sotto">Laboratorio di informatica &middot; IIS Marconi, Civitavecchia</p>
</div>
</header>
<p>Cerca il tuo nome e clicca per aprire la tua pagina.</p>
<input id="cerca" type="search" placeholder="Scrivi il tuo nome..." autofocus>
<ul id="elenco">
{voci}
</ul>
<script>
  var campo = document.getElementById("cerca");
  campo.addEventListener("input", function () {{
    var q = campo.value.toLowerCase();
    document.querySelectorAll("#elenco li").forEach(function (li) {{
      li.style.display = li.textContent.toLowerCase().indexOf(q) === -1 ? "none" : "";
    }});
  }});
</script>
</body>
</html>
"""


ESTENSIONI_LOGO = (".png", ".jpg", ".jpeg", ".svg", ".webp")


def trova_logo(cartella):
    """Cerca un file 'logo.<estensione>' nella cartella di uscita."""
    for estensione in ESTENSIONI_LOGO:
        if (cartella / f"logo{estensione}").is_file():
            return f"logo{estensione}"
    return None


def crea_indice(voci, logo=None):
    righe = []
    for nome, nome_file in sorted(voci, key=lambda v: v[0].lower()):
        righe.append(f'<li><a href="{nome_file}.html">{html.escape(nome)}</a></li>')
    if logo:
        riquadro_logo = f'<img class="logo" src="{logo}" alt="Logo IIS Marconi">'
    else:
        riquadro_logo = '<div class="logo logo-vuoto" aria-hidden="true"></div>'
    return PAGINA_INDICE.format(sicurezza=META_SICUREZZA, voci="\n".join(righe),
                                logo=riquadro_logo)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="file CSV scaricato da Google Moduli")
    p.add_argument("--uscita", default="sito", help="cartella di destinazione")
    p.add_argument("--immagini", help="cartella di immagini da copiare in uscita/immagini")
    p.add_argument("--logo", help="file del logo (quadrato) da mostrare nell'indice; "
                   "in alternativa copia a mano 'logo.png' in uscita/")
    p.add_argument("--col-nome", help="intestazione della colonna con il nome")
    p.add_argument("--col-codice", help="intestazione della colonna con il codice")
    p.add_argument("--escludi", nargs="*", default=[],
                   help="nomi di file (senza .html) da non pubblicare")
    a = p.parse_args()

    csv.field_size_limit(10_000_000)
    with open(a.csv, newline="", encoding="utf-8-sig") as f:
        righe = list(csv.reader(f))
    if len(righe) < 2:
        sys.exit("Il CSV non contiene risposte.")
    i_nome, i_codice = trova_colonne(righe[0], a.col_nome, a.col_codice)

    pagine = {}       # nome_file -> (nome visibile, codice)
    avvisi = []
    for n, riga in enumerate(righe[1:], start=2):
        if len(riga) <= max(i_nome, i_codice):
            avvisi.append(f"riga {n}: troppo corta, saltata")
            continue
        nome = pulisci_testo(riga[i_nome])
        codice = riga[i_codice].replace("\r\n", "\n").replace("\r", "\n").strip()
        if not codice:
            avvisi.append(f"riga {n} ({nome or 'senza nome'}): codice vuoto, saltata")
            continue
        if len(codice) > MAX_CARATTERI:
            avvisi.append(f"riga {n} ({nome}): codice troppo lungo, saltata")
            continue
        nome_file = crea_nome_file(nome)
        if not nome_file or nome_file in NOMI_RISERVATI:
            nuovo = (nome_file or "pagina") + "-studente"
            avvisi.append(f"riga {n} ({nome or 'senza nome'}): nome non utilizzabile, "
                          f"pubblicata come '{nuovo}'")
            nome_file = nuovo
        if nome_file in pagine:
            avvisi.append(f"riga {n} ({nome}): nome già presente, "
                          f"tengo questa versione più recente")
        pagine[nome_file] = (nome or nome_file, codice)

    uscita = Path(a.uscita)
    uscita.mkdir(parents=True, exist_ok=True)

    for nome_file in a.escludi:
        pagine.pop(nome_file, None)
        vecchio = uscita / f"{nome_file}.html"
        if vecchio.exists():
            vecchio.unlink()
            avvisi.append(f"{nome_file}: escluso e rimosso da '{uscita}'")

    da_controllare = []
    for nome_file, (nome, codice) in pagine.items():
        trovate = segnalazioni(codice)
        if trovate:
            da_controllare.append((nome_file, trovate))
        (uscita / f"{nome_file}.html").write_text(inietta_sicurezza(codice),
                                                  encoding="utf-8")

    if a.logo:
        file_logo = Path(a.logo)
        if file_logo.suffix.lower() in ESTENSIONI_LOGO and file_logo.is_file():
            for vecchio in uscita.glob("logo.*"):
                vecchio.unlink()
            shutil.copy(file_logo, uscita / f"logo{file_logo.suffix.lower()}")
        else:
            avvisi.append(f"logo '{a.logo}' non trovato o formato non valido "
                          f"(usa {', '.join(ESTENSIONI_LOGO)})")
    logo = trova_logo(uscita)
    if not logo:
        avvisi.append("logo non presente: l'indice mostra un riquadro vuoto. "
                      "Usa --logo file.png oppure copia 'logo.png' in "
                      f"'{uscita}' e rilancia lo script")

    voci = [(nome, nome_file) for nome_file, (nome, _) in pagine.items()]
    (uscita / "index.html").write_text(crea_indice(voci, logo), encoding="utf-8")

    if a.immagini:
        sorgente = Path(a.immagini)
        if sorgente.is_dir():
            shutil.copytree(sorgente, uscita / "immagini", dirs_exist_ok=True)
        else:
            avvisi.append(f"cartella immagini '{a.immagini}' non trovata")

    print(f"Pubblicate {len(pagine)} pagine in '{uscita}' (più index.html).")
    if avvisi:
        print("\nAvvisi:")
        for s in avvisi:
            print("  -", s)
    if da_controllare:
        print("\nDA CONTROLLARE a mano prima di mettere online:")
        for nome_file, trovate in da_controllare:
            print(f"  - {nome_file}.html: " + "; ".join(trovate))
        print("Per toglierne una: rilancia con --escludi nome-del-file")
    else:
        print("\nNessuna pagina con elementi sospetti.")


if __name__ == "__main__":
    main()