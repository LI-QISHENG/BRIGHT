<img width="257" height="28" alt="image" src="https://github.com/user-attachments/assets/c32ba431-775e-443d-9525-eb985f83260d" /><img width="219" height="28" alt="image" src="https://github.com/user-attachments/assets/9dc28cb6-a7a5-4381-8153-614b1d0aaaf6" /># BRIGHT
Bacterial Risk Identification and Gene-based Health Toolkit (BRIGHT) is a metagenome-based platform for human pathogenic bacteria (HPB) risk identification. It enables one-click identification of potential HPB, quantitative risk assessment, disease association analysis, and pathogenic gene detection. BRIGHT further supports gene-based identification of bacteria with high human pathogenic risk and integrates machine learning models to associate high-risk bacteria with environmental factors.

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
   - mobileOG-db
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
Potential pathogenic gene files: VF.category.tsv, VF.type.tsv, KO.PathwayL2.tsv, ARG.type.tsv, mge_ARG_co.tsv and mge_VFG_co.tsv
```


Copyright 2025-2026 Qisheng Li, qs.li@cqu.edu.cn, Chongqing University, China;
                    Huan Liu, huanliu@cqu.edu.cn, Chongqing University, China;
                    Meng Liu, liumeng@cqu.edu.cn, Chongqing University, China.
