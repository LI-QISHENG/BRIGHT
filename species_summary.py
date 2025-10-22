#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import csv
import re

RANK_ORDER = ["Domain", "Phylum", "Class", "Order", "Family", "Genus", "Species"]
PREFIX2RANK = {"d__": "Domain","p__": "Phylum","c__": "Class","o__": "Order","f__": "Family","g__": "Genus","s__": "Species"}
SUFFIX_RE = re.compile(r"_(?:[A-Za-z]+)$")

def strip_suffix(name: str) -> str:
    if not name:
        return name
    return SUFFIX_RE.sub("", name)

def clean_genus(name: str) -> str:
    return strip_suffix(name.strip())

def clean_species(name: str) -> str:
    name = name.strip()
    if not name:
        return ""
    parts = name.split()
    if len(parts) >= 2:
        g = strip_suffix(parts[0])
        sp = strip_suffix(parts[1])
        return f"{g} {sp}"
    else:
        return strip_suffix(parts[0])

def parse_classification(cls: str):
    out = {r: "" for r in RANK_ORDER}
    if not cls or cls in ("N/A", "NA"):
        return out
    items = [t.strip() for t in cls.split(";") if t.strip()]
    for t in items:
        if "__" in t[:4]:
            pref, val = t[:3], t[3:]
            rank = PREFIX2RANK.get(pref)
            if rank:
                out[rank] = val.strip()
    out["Domain"] = out["Domain"].strip()
    out["Phylum"] = out["Phylum"].strip()
    out["Class"] = out["Class"].strip()
    out["Order"] = out["Order"].strip()
    out["Family"] = out["Family"].strip()
    out["Genus"] = clean_genus(out["Genus"])
    out["Species"] = clean_species(out["Species"])
    return out

def load_hpbdb(path: str):
    m = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            sp = (row.get("Species") or "").strip()
            bsl = (row.get("Biosafety level") or "").strip()
            if not sp:
                continue
            if bsl.lower() == "null":
                norm = "null"
            elif bsl.startswith("BSL-"):
                norm = bsl.replace("BSL-","",1)
            else:
                norm = bsl
            m[sp] = norm
    return m

def main():
    if len(sys.argv) < 4:
        sys.exit(1)
    infile = sys.argv[1]
    hpbdb = sys.argv[2]
    outfile = sys.argv[3]
    hpb_map = load_hpbdb(hpbdb)
    with open(infile, "r", encoding="utf-8", newline="") as f, open(outfile, "w", encoding="utf-8", newline="") as w:
        reader = csv.DictReader(f, delimiter="\t")
        writer = csv.writer(w, delimiter="\t")
        header = ["user_genome"] + RANK_ORDER + ["hpb_species","BSL"]
        writer.writerow(header)
        for row in reader:
            user = (row.get("user_genome") or "").strip()
            cls = (row.get("classification") or "").strip()
            ranks = parse_classification(cls)
            sp = ranks["Species"]
            if sp and sp in hpb_map:
                hpb = "Y"
                bsl = hpb_map[sp] if hpb_map[sp] != "" else "null"
            else:
                hpb = "N"
                bsl = "0"
            writer.writerow([user] + [ranks[r] for r in RANK_ORDER] + [hpb, bsl])

if __name__ == "__main__":
    main()
