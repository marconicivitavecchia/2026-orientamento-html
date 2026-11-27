#!/usr/bin/env bash
# prepara_immagini.sh
# Prende le foto scaricate da una cartella, le ridimensiona (max 800 px di
# larghezza), le converte in .jpg e normalizza i nomi: minuscolo, senza
# spazi, senza accenti e senza caratteri strani.
#
# Uso:    ./prepara_immagini.sh cartella_origine [cartella_destinazione]
# Esempio: ./prepara_immagini.sh ~/Downloads/foto-lab immagini
#
# Gli originali NON vengono toccati: il risultato va nella cartella di
# destinazione (di default "immagini", da copiare accanto a index.html).

set -euo pipefail

SRC="${1:-}"
DST="${2:-immagini}"
LARGHEZZA=800

if [ -z "$SRC" ] || [ ! -d "$SRC" ]; then
  echo "Uso: $0 cartella_origine [cartella_destinazione]" >&2
  exit 1
fi

# ImageMagick 7 si chiama "magick", la versione 6 "convert"
if command -v magick >/dev/null 2>&1; then
  IM=(magick)
elif command -v convert >/dev/null 2>&1; then
  IM=(convert)
else
  echo "ImageMagick non trovato. Installalo con: sudo apt install imagemagick" >&2
  exit 1
fi

mkdir -p "$DST"
shopt -s nullglob nocaseglob

conta=0
for f in "$SRC"/*.{jpg,jpeg,png,webp,heic}; do
  base=$(basename "$f")
  nome="${base%.*}"

  # minuscolo, accenti -> lettere semplici, tutto il resto -> trattino
  nuovo=$(printf '%s' "$nome" \
    | LC_ALL=C.UTF-8 iconv -f UTF-8 -t ASCII//TRANSLIT 2>/dev/null \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
  [ -z "$nuovo" ] && nuovo="immagine"

  # se esiste già un file con lo stesso nome, aggiunge un numero
  out="$DST/$nuovo.jpg"
  n=2
  while [ -e "$out" ]; do
    out="$DST/$nuovo-$n.jpg"
    n=$((n + 1))
  done

  # -auto-orient: raddrizza le foto da telefono; "800x>" riduce solo se più larga
  # lo sfondo bianco evita il nero al posto delle trasparenze dei PNG
  "${IM[@]}" "$f" -auto-orient -background white -flatten \
    -resize "${LARGHEZZA}x>" -quality 85 -strip "$out"

  echo "$base  ->  $(basename "$out")"
  conta=$((conta + 1))
done

echo
echo "Fatto: $conta immagini in '$DST'."
echo "Controlla i nomi: per la sfida 4 meglio nomi brevi e chiari (gatto.jpg, calcio.jpg)."
