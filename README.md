# BRIGHT
Bacterial Risk Identification and Gene-based Health Toolkit (BRIGHT) is a metagenome-based platform for human pathogenic bacteria risk identification.  It enables one-click identification of potential human pathogenic bacteria, risk quantification, disease association, and potential pathogenic gene detection.

## **Preparation**
1. **BRIGHT** is based on **conda** environment management. Please ensure the following tools are installed and configured before running the platform:
   - MEGAHIT  
   - MetaWRAP  
   - dRep  
   - CoverM  
   - HUMAnN3 (excluding databases)  
   - eggNOG  
   - GBDB-tk  
   - MetaVF_toolkit  
   - deepARG  
   - Esymicrobiome
2. The input data must be **paired-end metagenomic sequencing reads**
3. **metadata.txt** should be prepared.

## **Usage**
```bash
bash /path/to/BRIGHT.sh
```

## **Output**
BRIDGE provides multi-level human pathogenic bacteria risk outputs, including:
```bash
Bacterial and Disease risk file: species_level.tsv
Quantitative risk files: overall_risk.tsv, overall_risk_sample.tsv
Potential pathogenic gene files: VF.category.tsv, VF.type.tsv, KO.PathwayL2.tsv, ARG.type.tsv
```


Copyright 2025-2026 Qisheng Li, qs.li@cqu.edu.cn, Chongqing University, China;
                    HuanLiu, huanliu@cqu.edu.cn, Chongqing University, China;
                    Meng Liu, liumeng@cqu.edu.cn, Chongqing University, China.
