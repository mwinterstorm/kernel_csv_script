#!/usr/bin/env sh
set -euo pipefail

: "${INPUT_XLSX:?Set INPUT_XLSX to path of .xlsx in /data}"
: "${OUTPUT_CSV:=/data/out.csv}"
: "${SHEET:=Securities}"
: "${SKIPROWS:=2}"
: "${AMOUNT_COLUMNS:=col10,col8,col12,col11,col14,col15}"

exec python /app/parse_securities.py \
  "$INPUT_XLSX" "$OUTPUT_CSV" \
  --sheet "$SHEET" \
  --skiprows "$SKIPROWS" \
  --amount-columns "$AMOUNT_COLUMNS"
