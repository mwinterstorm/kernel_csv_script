#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import re
from pathlib import Path

BUY_SELL_RE = re.compile(r'^(Buy|Sell)\s+([\d,\.]+)\s+(.*?)\s+at\s+([\d,\.]+)\s*$', re.IGNORECASE)
REINVEST_RE = re.compile(r'^(Reinvest)\s+(.*?)\s+at\s+([\d,\.]+)\s*$', re.IGNORECASE)

def num(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip().replace(',', '')
    try:
        return float(s)
    except Exception:
        return None

def parse_one_row(row, amount_columns):
    desc = str(row.get('col5', '')).strip()
    desc_norm = re.sub(r'\s+', ' ', desc)

    date_raw = row.get('col3', None)
    date_iso = None
    if pd.notna(date_raw):
        try:
            date_iso = pd.to_datetime(date_raw).date().isoformat()
        except Exception:
            date_iso = str(date_raw)

    total = None
    for c in amount_columns:
        v = num(row.get(c))
        if v is not None and np.isfinite(v):
            total = v
            break

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
            if total is not None and unit_price not in (None, 0):
                units = round(total / unit_price, 8)
        else:
            return None

    return {
        'date': date_iso,
        'units': units,
        'type': typ,
        'unitPrice': unit_price,
        'ticker': ticker,
        'total': total,
    }

def parse_workbook(xlsx_path, sheet, skiprows, amount_columns):
    # Load and normalise columns
    df = pd.read_excel(xlsx_path, sheet_name=sheet, skiprows=skiprows)
    df.columns = [f"col{i}" for i in range(len(df.columns))]
    desc = df.get('col5')
    if desc is None:
        return pd.DataFrame(columns=['date','units','type','unitPrice','ticker','total'])

    trade_mask = desc.astype(str).str.contains(r'\b(Buy|Sell|Reinvest)\b', case=False, na=False)
    trades = df[trade_mask].copy()

    out_rows = []
    for _, row in trades.iterrows():
        rec = parse_one_row(row, amount_columns)
        if rec:
            out_rows.append(rec)

    return pd.DataFrame(out_rows, columns=['date','units','type','unitPrice','ticker','total'])

def main():
    ap = argparse.ArgumentParser(description="Parse all Kernel GL 'Securities' trades from a folder of Excel files.")
    ap.add_argument('--input-dir', default='/input', help='Directory containing .xlsx files')
    ap.add_argument('--output-file', default='/output/kernel_trades.csv', help='Single CSV to write')
    ap.add_argument('--sheet', default='Securities', help='Sheet name')
    ap.add_argument('--skiprows', type=int, default=2, help='Header rows to skip')
    ap.add_argument('--amount-columns', default='col10,col8,col12,col11,col14,col15',
                    help='Comma-separated column ids to search for total')
    ap.add_argument('--pattern', default='*.xlsx', help='Glob for files (default: *.xlsx)')
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    files = sorted([p for p in in_dir.glob(args.pattern)
                    if p.is_file() and not p.name.startswith('~$')])  # ignore Excel temp files

    if not files:
        raise SystemExit(f"No files matching {args.pattern} in {in_dir}")

    amount_cols = [c.strip() for c in args.amount_columns.split(',') if c.strip()]

    all_frames = []
    for f in files:
        try:
            df = parse_workbook(f, args.sheet, args.skiprows, amount_cols)
            if not df.empty:
                all_frames.append(df)
        except Exception as e:
            print(f"[WARN] Skipping {f.name}: {e}")

    if not all_frames:
        print("No trades found in any files.")
        pd.DataFrame(columns=['date','units','type','unitPrice','ticker','total']).to_csv(args.output_file, index=False)
        return

    out = pd.concat(all_frames, ignore_index=True)
    # sort if possible
    try:
        out['_d'] = pd.to_datetime(out['date'])
        out = out.sort_values('_d').drop(columns=['_d'])
    except Exception:
        pass

    out.to_csv(args.output_file, index=False)
    print(f"Wrote {len(out)} rows -> {args.output_file}")

if __name__ == '__main__':
    main()