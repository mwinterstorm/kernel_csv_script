#!/usr/bin/env sh
set -eu 

: "${INPUT_DIR:=/input}"
: "${OUTPUT_FILE:=/output/kernel_trades.csv}"
: "${SHEET:=Securities}"
: "${SKIPROWS:=2}"
: "${AMOUNT_COLUMNS:=col10,col8,col12,col11,col14,col15}"
: "${PATTERN:=*.xlsx}"

exec python /app/parse_securities.py \
  --input-dir "$INPUT_DIR" \
  --output-file "$OUTPUT_FILE" \
  --sheet "$SHEET" \
  --skiprows "$SKIPROWS" \
  --amount-columns "$AMOUNT_COLUMNS" \
  --pattern "$PATTERN"