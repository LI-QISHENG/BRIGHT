# -*- coding: utf-8 -*-

import sys
import re
import csv

import pandas as pd

def read_emapper_ko(emapper_path: str) -> pd.DataFrame:
    # Read lines, find header line '#query ...', then read as TSV
    header_idx = None
    with open(emapper_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith('#query'):
            header_idx = i
            break
    if header_idx is None:
        raise RuntimeError("Cannot find header line starting with '#query' in emapper file.")

    # Build DataFrame from the header onward
    from io import StringIO
    tsv_text = ''.join(lines[header_idx:])  # include header
    df = pd.read_csv(StringIO(tsv_text), sep='\t', dtype=str, quoting=csv.QUOTE_NONE)
    # Normalize column names (some eggNOG versions slightly vary)
    # We expect 'KEGG_ko' column; if absent, try alternatives.
    if 'KEGG_ko' not in df.columns:
        # Try lowercase or other variants
        candidates = [c for c in df.columns if c.lower() == 'kegg_ko']
        if candidates:
            df.rename(columns={candidates[0]: 'KEGG_ko'}, inplace=True)
        else:
            raise RuntimeError("Column 'KEGG_ko' not found in emapper file.")
    return df[['KEGG_ko']]

def extract_kos(ko_series: pd.Series) -> pd.DataFrame:
    # Collect unique KO IDs like Kxxxxx (remove 'ko:' prefix)
    pat = re.compile(r'K\d{5}')
    kos = set()
    for val in ko_series.fillna(''):
        if val == '-' or val.strip() == '':
            continue
        # split by comma and/or semicolon
        parts = re.split(r'[,\s;]+', val.strip())
        for p in parts:
            # strip possible 'ko:' prefix
            m = pat.search(p)
            if m:
                kos.add(m.group(0))
    return pd.DataFrame(sorted(kos), columns=['KO'])

def main():
    if len(sys.argv) < 3:
        print("Usage: python genome_ko_table.py output.emapper.annotations KO1-4.txt [genome_KO_pathways.csv]", file=sys.stderr)
        sys.exit(1)
    emapper_path = sys.argv[1]
    ko_map_path  = sys.argv[2]
    out_csv      = sys.argv[3] if len(sys.argv) >= 4 else 'genome_KO_pathways.csv'

    # 1) read emapper KOs
    df_em = read_emapper_ko(emapper_path)
    df_kos = extract_kos(df_em['KEGG_ko'])

    if df_kos.empty:
        # Create empty CSV with header
        pd.DataFrame(columns=['KO','PathwayL1','PathwayL2','Pathway','KoDescription']).to_csv(out_csv, index=False)
        print(f"No KO terms found. Wrote empty table with header to {out_csv}")
        return

    # 2) read KO ¡ú pathway mapping (tab-delimited)
    df_map = pd.read_csv(ko_map_path, sep='\t', dtype=str).fillna('')

    required_cols = {'KO','PathwayL1','PathwayL2','Pathway','KoDescription'}
    if not required_cols.issubset(set(df_map.columns)):
        missing = required_cols - set(df_map.columns)
        raise RuntimeError(f"KO mapping file missing columns: {missing}")

    # 3) merge
    df_out = df_kos.merge(df_map, how='left', on='KO')

    # Sort by KO for reproducibility
    df_out = df_out[['KO','PathwayL1','PathwayL2','Pathway','KoDescription']].sort_values('KO', kind='stable')

    # 4) write CSV
    df_out.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} with {len(df_out)} KO records.")

if __name__ == "__main__":
    main()
