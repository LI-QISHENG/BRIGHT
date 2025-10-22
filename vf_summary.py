#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, re, sys, glob, argparse
from collections import defaultdict, Counter
import pandas as pd

def split_smart(line: str):
    if "\t" in line:
        return line.rstrip("\n").split("\t")
    return re.split(r"\s{2,}", line.strip())

def norm_header_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[\s\|\-\(\)\[\]\{\}:/\\]+", "_", s)
    s = re.sub(r"[^0-9a-z_]+", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def infer_sample_id_from_path(path: str) -> str:
    d = os.path.basename(os.path.dirname(path)).strip()
    if d and d != ".":
        return d
    b = os.path.basename(path)
    for suf in (".summary",):
        if b.endswith(suf):
            return b[:-len(suf)]
    return os.path.splitext(b)[0]

def read_vf_categories(path: str):
    ctr = Counter()
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            header = None
            key_cat = None
            for raw in f:
                if not raw.strip():
                    continue
                if header is None:
                    header = split_smart(raw)
                    norm_map = {norm_header_name(c): c for c in header}
                    key_cat = norm_map.get("vf_category")
                    if key_cat is None:
                        for k_norm, k_orig in norm_map.items():
                            if "vf" in k_norm and "category" in k_norm:
                                key_cat = k_orig
                                break
                    if key_cat is None:
                        raise ValueError("VF_category column not found")
                    continue
                parts = split_smart(raw)
                if len(parts) < len(header):
                    parts += [""] * (len(header) - len(parts))
                data = dict(zip(header, parts))
                cat = (data.get(key_cat) or "").strip() or "Uncategorized"
                ctr[cat] += 1.0
    except Exception as e:
        print(f"[WARN] Failed to parse {path}: {e}", file=sys.stderr)
    return ctr

def format_number(x):
    try:
        xf = float(x)
        return str(int(xf)) if xf.is_integer() else f"{xf:.6g}"
    except Exception:
        return str(x)

def build_transposed(sum_map: dict, out_path: str):
    samples = sorted(sum_map.keys())
    features = set()
    for ctr in sum_map.values():
        features.update(ctr.keys())
    features = sorted(features)
    df = pd.DataFrame(0.0, index=features, columns=samples)
    for sid, ctr in sum_map.items():
        for feat, val in ctr.items():
            df.at[feat, sid] = df.at[feat, sid] + float(val)
    df["sum"] = df.sum(axis=1)
    col_sums = df.sum(axis=0)
    df.loc["sum"] = col_sums
    df_fmt = df.applymap(format_number)
    df_fmt.index.name = ""
    df_fmt.to_csv(out_path, sep="\t", header=True, index=True)

def main():
    ap = argparse.ArgumentParser(description="Summarize *.summary VF_category counts per sample to VF.category.tsv")
    ap.add_argument("files", nargs="*", help="Input files (shell-expanded).")
    ap.add_argument("--pattern", default="*/*.summary", help="Glob pattern (default: */*.summary)")
    ap.add_argument("--out-prefix", default="", help="Output prefix, e.g. 'results/'")
    args = ap.parse_args()

    files = args.files if args.files else glob.glob(args.pattern)
    files = sorted(set(files))
    if not files:
        print("[ERROR] No input files found.", file=sys.stderr)
        sys.exit(1)

    sample_to_cat = defaultdict(Counter)
    for path in files:
        sid = infer_sample_id_from_path(path)
        ctr = read_vf_categories(path)
        if not ctr:
            continue
        sample_to_cat[sid].update(ctr)

    out_cat = f"{args.out_prefix}VF.category.tsv"
    build_transposed(sample_to_cat, out_cat)
    print(f"[OK] Wrote: {out_cat}")

if __name__ == "__main__":
    main()