#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import argparse
from collections import Counter, defaultdict
import pandas as pd

def infer_sample_id(path: str, mode: str) -> str:
    if mode == 'parent':
        parent = os.path.basename(os.path.dirname(path)).strip()
        if parent and parent != '.':
            return parent
    base = os.path.basename(path)
    return base[:-len('.ko.disease')] if base.endswith('.ko.disease') else os.path.splitext(base)[0]

def read_ko_disease(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, dtype=str)  # robust to quoted commas
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV: {e}")
    required = {'KO','PathwayL1','PathwayL2','Pathway','KoDescription'}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing columns: {missing}")
    df['PathwayL2'] = df['PathwayL2'].fillna('').astype(str).str.strip()
    return df

def format_number(x):
    try:
        xf = float(x)
        return str(int(xf)) if xf.is_integer() else f"{xf:.6g}"
    except Exception:
        return str(x)

def build_transposed_table(sample_to_counter: dict, out_path: str):
    samples = sorted(sample_to_counter.keys())
    features = set()
    for c in sample_to_counter.values():
        features.update(c.keys())
    features = sorted(features)

    df = pd.DataFrame(0.0, index=features, columns=samples)
    for sid, ctr in sample_to_counter.items():
        for feat, val in ctr.items():
            df.at[feat, sid] = df.at[feat, sid] + float(val)

    df['sum'] = df.sum(axis=1)
    col_sums = df.sum(axis=0)     
    df.loc['sum'] = col_sums

    df_fmt = df.applymap(format_number)
    df_fmt.index.name = 'PathwayL2'    
    df_fmt.to_csv(out_path, sep='\t', header=True, index=True)

def main():
    ap = argparse.ArgumentParser(description="Summarize *.ko.disease into a PathwayL2 x sample table with row/col sums.")
    ap.add_argument('files', nargs='*', help="Input files (shell-expanded).")
    ap.add_argument('--pattern', default='*/*.ko.disease', help="Glob pattern if files not given (default: '*/*.ko.disease').")
    ap.add_argument('--out-prefix', default='', help="Output prefix, e.g. 'results/'.")
    ap.add_argument('--sample-mode', choices=['basename','parent'], default='basename',
                    help="How to infer sample ID: 'basename' (file name without .ko.disease) or 'parent' (parent directory). Default: basename.")
    args = ap.parse_args()

    files = args.files if args.files else glob.glob(args.pattern)
    files = sorted(set(files))
    if not files:
        print("[ERROR] No input files found. Provide files or adjust --pattern.", file=sys.stderr)
        sys.exit(1)

    sample_to_counter = defaultdict(Counter)

    for path in files:
        sid = infer_sample_id(path, args.sample_mode)
        try:
            df = read_ko_disease(path)
        except Exception as e:
            print(f"[WARN] {sid}: {e}", file=sys.stderr)
            continue

        counts = df.groupby('PathwayL2', dropna=False).size()
        for p2, cnt in counts.items():
            name = (p2 or 'NA').strip()
            sample_to_counter[sid][name] += float(cnt)

    out_path = f"{args.out_prefix}KO.PathwayL2.tsv"
    build_transposed_table(sample_to_counter, out_path)
    print(f"[OK] Wrote: {out_path}")
    print(f"[INFO] Samples ({len(sample_to_counter)}): " + ", ".join(sorted(sample_to_counter.keys())))

if __name__ == '__main__':
    main()
