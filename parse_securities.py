#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path

BUY_SELL_RE = re.compile(r'^(Buy|Sell)\s+([\d,\.]+)\s+(.*?)\s+at\s+([\d,\.]+)\s*$', re.IGNORECASE)
REINVEST_RE = re.compile(r'^(Reinvest)\s+(.*?)\s+at\s+([\d,\.]+)\s*$', re.IGNORECASE)

def num(x):
    """Convert str with commas to float; return None on failure."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip().replace(',', '')
    try:
        return float(s)
    except Exception:
        return None

def parse_row(row, amount_columns):
    """
    Row comes from the sheet after skiprows=2 with columns renamed to col0..colN.
    Description is in col5 in these Kernel reports; we detect trades by matching
    'Buy|Sell|Reinvest' in that description string.
    """
    desc = str(row.get('col5', '')).strip()
    # Normalize multiple spaces (without breaking fund name)
    desc_norm = re.sub(r'\s+', ' ', desc)

    # Date is in col3 (e.g. '14 Jul 2025')
    date_raw = row.get('col3', None)
    date_iso = None
    if pd.notna(date_raw):
        try:
            date_iso = pd.to_datetime(date_raw).date().isoformat()
        except Exception:
            # Leave as-is if it fails to parse
            date_iso = str(date_raw)

    # Try to locate total amount from typical numeric columns on these reports
    total = None
    for c in amount_columns:
        v = num(row.get(c))
        if v is not None and np.isfinite(v):
            total = v
            break

    # Parse description
    typ, units, unit_price, ticker = None, None, None, None

    m = BUY_SELL_RE.match(desc_norm)
    if m:
        typ = m.group(1).title()
        units = num(m.group(2))
        ticker = m.group(3).strip()
        unit_price = num(m.group(4))
    else:
        m2 = REINVEST_RE.match(desc_norm)
        if m2:
            typ = 'Reinvest'
            ticker = m2.group(2).strip()
            unit_price = num(m2.group(3))
            # Units not present in text; compute if possible
            if total is not None and unit_price not in (None, 0):
                units = round(total / unit_price, 8)
        else:
            # Not a trade line we understand
            return None

    return {
        'date': date_iso,
        'units': units,
        'type': typ,
        'unitPrice': unit_price,
        'ticker': ticker,
        'total': total,
    }

def main():
    parser = argparse.ArgumentParser(description="Parse trades from the 'Securities' tab of a Kernel GL Excel.")
    parser.add_argument('xlsx', help='Path to the Excel file')
    parser.add_argument('out_csv', help='Where to write the parsed CSV')
    parser.add_argument('--sheet', default='Securities', help='Sheet name (default: Securities)')
    parser.add_argument(
        '--amount-columns',
        default='col10,col8,col12,col11,col14,col15',
        help='Comma-separated list of column ids (after renaming to col0..colN) to scan for Total amount in order of preference'
    )
    parser.add_argument('--skiprows', type=int, default=2, help='Rows to skip at top (default: 2)')
    args = parser.parse_args()

    xlsx_path = Path(args.xlsx)
    if not xlsx_path.exists():
        raise SystemExit(f"File not found: {xlsx_path}")

    # Read the sheet. These GL exports usually have two header/metadata rows.
    df = pd.read_excel(xlsx_path, sheet_name=args.sheet, skiprows=args.skiprows)
    df.columns = [f"col{i}" for i in range(len(df.columns))]

    # Filter rows that look like trade descriptions in col5
    desc = df.get('col5')
    if desc is None:
        raise SystemExit("Could not find description column (expected col5 after renaming).")

    trade_mask = desc.astype(str).str.contains(r'\b(Buy|Sell|Reinvest)\b', case=False, na=False)
    trades = df[trade_mask].copy()

    amount_cols = [c.strip() for c in args.amount_columns.split(',') if c.strip()]

    parsed_rows = []
    for _, row in trades.iterrows():
        rec = parse_row(row, amount_cols)
        if rec is not None:
            parsed_rows.append(rec)

    if not parsed_rows:
        print("No trade rows parsed. Check --skiprows or the regex patterns.")
        # still write an empty CSV with headers for consistency
        out = pd.DataFrame(columns=['date','units','type','unitPrice','ticker','total'])
        out.to_csv(args.out_csv, index=False)
        return

    out = pd.DataFrame(parsed_rows, columns=['date','units','type','unitPrice','ticker','total'])
    # Sort by date if parseable
    try:
        out['_d'] = pd.to_datetime(out['date'])
        out = out.sort_values('_d').drop(columns=['_d'])
    except Exception:
        pass

    out.to_csv(args.out_csv, index=False)
    print(f"Wrote {len(out)} rows -> {args.out_csv}")

if __name__ == '__main__':
    main()
