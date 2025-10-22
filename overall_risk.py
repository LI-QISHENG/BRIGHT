#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import pandas as pd
from collections import defaultdict

def read_sum_row(path):
    df = pd.read_csv(path, sep="\t", dtype=str)
    if df.shape[1] == 0:
        return {}
    df = df.set_index(df.columns[0])
    if "sum" in df.index:
        s = df.loc["sum"]
    else:
        num = df.apply(pd.to_numeric, errors="coerce")
        s = num.sum(axis=0)
    if "sum" in s.index:
        s = s.drop(labels=["sum"])
    s = pd.to_numeric(s, errors="coerce").fillna(0)
    return s.to_dict()

def main():
    if len(sys.argv) < 6:
        sys.exit(1)
    species_tsv = sys.argv[1]
    vf_cat_tsv = sys.argv[2]
    ko_p2_tsv = sys.argv[3]
    arg_type_tsv = sys.argv[4]
    out_tsv = sys.argv[5]

    sp = pd.read_csv(species_tsv, sep="\t", dtype=str).fillna("")
    if "user_genome" not in sp.columns:
        sys.exit(2)
    if "Disease" not in sp.columns:
        sp["Disease"] = ""

    vf_map = read_sum_row(vf_cat_tsv)
    ko_map = read_sum_row(ko_p2_tsv)
    arg_map = read_sum_row(arg_type_tsv)

    def mget(d, k):
        v = d.get(k, 0)
        try:
            return int(float(v)) if float(v).is_integer() else float(v)
        except Exception:
            return 0

    sp["VF_gene_sum"] = [mget(vf_map, x) for x in sp["user_genome"]]
    sp["KO_PathwayL2_sum"] = [mget(ko_map, x) for x in sp["user_genome"]]
    sp["ARG_gene_sum"] = [mget(arg_map, x) for x in sp["user_genome"]]

    sp["VF_gene_sum"] = pd.to_numeric(sp["VF_gene_sum"], errors="coerce").fillna(0)
    sp["KO_PathwayL2_sum"] = pd.to_numeric(sp["KO_PathwayL2_sum"], errors="coerce").fillna(0)
    sp["ARG_gene_sum"] = pd.to_numeric(sp["ARG_gene_sum"], errors="coerce").fillna(0)

    sp["Overall_risk"] = sp["VF_gene_sum"] * sp["KO_PathwayL2_sum"] * (1 + sp["ARG_gene_sum"])

    ranks = ["Species","Genus","Family","Order","Class","Phylum","Domain","user_genome"]
    base_names = []
    for _, row in sp.iterrows():
        name = ""
        for r in ranks:
            val = (row.get(r) if r in sp.columns else "") or ""
            val = str(val).strip()
            if val:
                name = val
                break
        base_names.append(name if name else "MAG")
    counts = defaultdict(int)
    mag_names = []
    for nm in base_names:
        counts[nm] += 1
        if counts[nm] == 1:
            mag_names.append(nm)
        else:
            mag_names.append(f"{nm}({counts[nm]})")
    if "Species" in sp.columns:
        idx = sp.columns.get_loc("Species") + 1
        sp.insert(idx, "MAG_name", mag_names)
    else:
        sp.insert(1, "MAG_name", mag_names)

    sp.to_csv(out_tsv, sep="\t", index=False)

if __name__ == "__main__":
    main()
