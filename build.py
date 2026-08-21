#!/usr/bin/env python3
"""Sincronizza la sorgente con il bundle PWA.
La sorgente è copenaghen-2026.html (tenuta ferma per non cambiare l'URL dell'artifact).
index.html è la stessa cosa, con il nome che serve a un hosting web."""
import shutil, pathlib
src = pathlib.Path("copenaghen-2026.html")
shutil.copyfile(src, "index.html")
print("index.html aggiornato da", src, "-", src.stat().st_size, "byte")
