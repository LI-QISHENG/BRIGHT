# -*- coding: utf-8 -*-

import sys
import re
import csv
import pandas as pd

def parse_args(argv):
    argv = list(argv)  # copy
    hd = False
    # accept -hd anywhere
    if "-hd" in argv:
        hd = True
        argv.remove("-hd")

    if len(argv) < 3:
        print("Usage: python genome_ko_table.py output.emapper.annotations KO1-4.txt [genome_KO_pathways.csv] [-hd]", file=sys.stderr)
        sys.exit(1)

    emapper_path = argv[1]
    ko_map_path  = argv[2]
    out_csv      = argv[3] if len(argv) >= 4 else None

    if out_csv is None:
        out_csv = "genome_KO_pathways_HumanDiseases.csv" if hd else "genome_KO_pathways.csv"

    return emapper_path, ko_map_path, out_csv, hd

def read_emapper_ko(emapper_path: str) -> pd.DataFrame:
    header_idx = None
    with open(emapper_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith('#query'):
            header_idx = i
            break
    if header_idx is None:
        raise RuntimeError("Cannot find header line starting with '#query' in emapper file.")

    from io import StringIO
    tsv_text = ''.join(lines[header_idx:])
    df = pd.read_csv(StringIO(tsv_text), sep='\t', dtype=str, quoting=csv.QUOTE_NONE)
    if 'KEGG_ko' not in df.columns:
        candidates = [c for c in df.columns if c.lower() == 'kegg_ko']
        if candidates:
            df = df.rename(columns={candidates[0]: 'KEGG_ko'})
        else:
            raise RuntimeError("Column 'KEGG_ko' not found in emapper file.")
    return df[['KEGG_ko']]

def extract_kos(ko_series: pd.Series) -> pd.DataFrame:
    pat = re.compile(r'K\d{5}')
    kos = set()
    for val in ko_series.fillna(''):
        if val == '-' or val.strip() == '':
            continue
        parts = re.split(r'[,\s;]+', val.strip())
        for p in parts:
            m = pat.search(p)
            if m:
                kos.add(m.group(0))
    return pd.DataFrame(sorted(kos), columns=['KO'])

def main():
    emapper_path, ko_map_path, out_csv, hd = parse_args(sys.argv)

    # 1) KOs from emapper
    df_em = read_emapper_ko(emapper_path)
    df_kos = extract_kos(df_em['KEGG_ko'])

    # Prepare empty header if no KO found
    header_cols = ['KO','PathwayL1','PathwayL2','Pathway','KoDescription']
    if df_kos.empty:
        pd.DataFrame(columns=header_cols).to_csv(out_csv, index=False)
        print(f"No KO terms found. Wrote empty table with header to {out_csv}")
        return

    # 2) KO map
    df_map = pd.read_csv(ko_map_path, sep='\t', dtype=str).fillna('')
    required_cols = set(header_cols)
    missing = required_cols - set(df_map.columns)
    if missing:
        raise RuntimeError(f"KO mapping file missing columns: {missing}")

    # 3) merge
    df_out = df_kos.merge(df_map, how='left', on='KO')[header_cols].sort_values('KO', kind='stable')

    # 4) optional filter: Human Diseases only
    if hd:
        df_out = df_out[df_out['PathwayL1'] == 'Human Diseases'].copy()

    # 5) write
    df_out.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} with {len(df_out)} KO records{' (Human Diseases only)' if hd else ''}.")

if __name__ == "__main__":
    main()
