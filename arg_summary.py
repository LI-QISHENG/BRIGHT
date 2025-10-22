#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from collections import defaultdict, Counter
import pandas as pd

def infer_sample_id(path: str) -> str:
    base = os.path.basename(path)
    if base.endswith(".mapping.ARG"):
        return base[:-len(".mapping.ARG")]
    return os.path.splitext(base)[0]

def parse_file(path: str, type_counter: Counter, gene_counter: Counter, type_gene_counter: dict):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 12:
                    continue

                arg_first = parts[0]
                predicted_class = parts[4]
                best_hit = parts[5]
                counts_str = parts[-1]
                try:
                    cnt = float(counts_str)
                except ValueError:
                    cnt = 1.0

                arg_type = None
                arg_gene = None

                if "|" in best_hit:
                    toks = best_hit.split("|")
                    if len(toks) >= 2:
                        arg_gene = toks[-1].strip()
                        arg_type = toks[-2].strip()

                if not arg_type:
                    arg_type = predicted_class.strip()
                if not arg_gene:
                    arg_gene = arg_first.strip()

                type_counter[arg_type] += cnt
                gene_counter[arg_gene] += cnt
                type_gene_counter[arg_type][arg_gene] += cnt

    except Exception as e:
        print(f"[WARN] {path}: {e}", file=sys.stderr)

def format_number(x: float) -> str:
    try:
        xf = float(x)
        return str(int(xf)) if xf.is_integer() else f"{xf:.6g}"
    except Exception:
        return str(x)

def write_transposed_table(out_path: str, sample_to_counter: dict):
    samples = sorted(sample_to_counter.keys())
    features = set()
    for ctr in sample_to_counter.values():
        features.update(ctr.keys())
    features = sorted(features)
    if not samples or not features:
        pd.DataFrame({"": ["sum"], "sum": [0]}).set_index("").to_csv(out_path, sep="\t")
        return

    df = pd.DataFrame(0.0, index=features, columns=samples)
    for sid, ctr in sample_to_counter.items():
        for feat, val in ctr.items():
            df.at[feat, sid] = df.at[feat, sid] + float(val)

    df["sum"] = df.sum(axis=1)
    col_sums = df.sum(axis=0)
    df.loc["sum"] = col_sums

    df_str = df.applymap(format_number)
    df_str.index.name = ""
    df_str.to_csv(out_path, sep="\t", header=True, index=True)

def write_matrix_table(out_path: str, type_gene_counter: dict):
    types = sorted(type_gene_counter.keys())
    genes = sorted({g for t in type_gene_counter.values() for g in t.keys()})
    if not types or not genes:
        pd.DataFrame({"": ["sum"], "sum": [0]}).set_index("").to_csv(out_path, sep="\t")
        return

    df = pd.DataFrame(0.0, index=types, columns=genes)
    for t, gctr in type_gene_counter.items():
        for g, v in gctr.items():
            df.at[t, g] = df.at[t, g] + float(v)

    df["sum"] = df.sum(axis=1)
    col_sums = df.sum(axis=0)
    df.loc["sum"] = col_sums

    df_str = df.applymap(format_number)
    df_str.index.name = ""
    df_str.to_csv(out_path, sep="\t", header=True, index=True)

def main():
    ap = argparse.ArgumentParser(
        description="Summarize DeepARG-GONG *.mapping.ARG into ARG.type.tsv, ARG.gene.tsv, and ARG.sanky.tsv"
    )
    ap.add_argument("files", nargs="+", help="Input *.mapping.ARG files")
    ap.add_argument("--out-prefix", default="", help="Optional prefix for output files")
    args = ap.parse_args()

    sample_to_type = defaultdict(Counter)
    sample_to_gene = defaultdict(Counter)
    type_gene_counter = defaultdict(Counter)

    for path in args.files:
        sid = infer_sample_id(path)
        type_ctr = Counter()
        gene_ctr = Counter()
        parse_file(path, type_ctr, gene_ctr, type_gene_counter)
        sample_to_type[sid].update(type_ctr)
        sample_to_gene[sid].update(gene_ctr)

    out_type = f"{args.out_prefix}ARG.type.tsv"
    out_gene = f"{args.out_prefix}ARG.gene.tsv"
    out_sanky = f"{args.out_prefix}ARG.sanky.tsv"

    write_transposed_table(out_type, sample_to_type)
    write_transposed_table(out_gene, sample_to_gene)
    write_matrix_table(out_sanky, type_gene_counter)

    print(f"[OK] Wrote: {out_type}")
    print(f"[OK] Wrote: {out_gene}")
    print(f"[OK] Wrote: {out_sanky}")

if __name__ == "__main__":
    main()