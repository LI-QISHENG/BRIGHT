#Genome data acquisition
##Quality control
mkdir -p bright bright/temp bright/result
cd bridge
mkdir -p temp/qc
time tail -n+2 metadata.txt|cut -f1|rush -j 16 \
  "fastp -i seq/{1}_1.fq.gz -I seq/{1}_2.fq.gz \
    -j temp/qc/{1}_fastp.json -h temp/qc/{1}_fastp.html \
    -o temp/qc/{1}_1.fastq  -O temp/qc/{1}_2.fastq \ 
    > temp/qc/{1}.log 2>&1 "

##Assembly
conda activate megahit
mkdir -p result/megahit
while IFS= read -r sample_name; do
    megahit -t 64 --k-min 29 --k-max 149 --k-step 20 \
        -1 "temp/qc/${sample_name}_1.fastq" \
        -2 "temp/qc/${sample_name}_2.fastq" \
        -o temp/megahit
    mv temp/megahit/log "result/megahit/${sample_name}.log"
    mv temp/megahit/final.contigs.fa "result/megahit/${sample_name}final.contigs.fa"
    rm -rf temp/megahit
done < <(tail -n +2 metadata.txt | cut -f1)

##Binning
conda activate metawrap
mkdir -p temp/binning
time tail -n+2 metadata.txt|cut -f1|rush -j 4 \
    "metawrap binning \
        -o temp/binning/{} -t 32 \
        -a result/megahit/{}final.contigs.fa \
        --metabat2 --maxbin2 --concoct temp/qc/{}_*.fastq > /dev/null 2>&1"

mkdir -p temp/bin_refinement
time tail -n+2 metadata.txt|cut -f1|rush -j 4 \
    "metawrap bin_refinement \
       -o temp/bin_refinement/{} -t 32 \
       -A temp/binning/{}/metabat2_bins/ \
       -B temp/binning/{}/maxbin2_bins/ \
       -C temp/binning/{}/concoct_bins/ \
       -c 55 -x 5 "

mkdir -p temp/drep_in
for i in `tail -n+2 metadata.txt|cut -f1`;do
    ln -s `pwd`/temp/bin_refinement/${i}/metawrap_55_5_bins/bin.* temp/drep_in/
    rename "s/bin./Sg_${i}_/" temp/drep_in/bin.*
done
/bin/rm -f temp/drep_in/*\*

##MAG acquisition
conda activate dRep
mkdir -p temp/drep95
dRep dereplicate temp/drep95/ \
    -g temp/drep_in/*.fa  \
    -sa 0.95 -nc 0.30 -comp 55 -con 5 -p 64

conda activate coverm
mkdir -p temp/coverm result/coverm
tail -n+2 metadata.txt|cut -f1|rush -j 4 \
    "coverm genome --coupled temp/qc/{}_1.fastq temp/qc/{}_2.fastq \
        --genome-fasta-directory temp/drep95/dereplicated_genomes/ -x fa \
        -o temp/coverm/{}.txt -t 32"

conda activate humann3
sed -i 's/_1.fastq Relative Abundance (%)//' temp/coverm/*.txt
humann_join_tables --input temp/coverm \
    --file_name txt \
    --output result/coverm/MAGabundance.tsv 

echo "SampleID" > metadataS.txt
ls temp/drep95/dereplicated_genomes/|sed 's/\.fa//' >> metadataS.txt

conda activate eggnog
mkdir -p temp/prodigal temp/MAG_nucleotide temp/MAG_protein temp/MAG_nucleotide2
tail -n+2 metadataS.txt|cut -f1|rush -j 6 \
"prodigal \
    -i temp/drep95/dereplicated_genomes/{1}.fa \
    -o temp/prodigal/{1}.gff  \
    -a temp/prodigal/{1}.faa \
    -d temp/prodigal/{1}.ffn \
    -p single -f gff" 

rules="
faa temp/MAG_protein fa
ffn temp/MAG_nucleotide fa
ffn temp/MAG_nucleotide2 fna
"
for rule in $rules; do
  set -- $rule
  ext=$1; outdir=$2; newext=$3
  for f in temp/prodigal/*.$ext; do
    [ -e "$f" ] || continue
    base=$(basename "$f" .$ext)
    cp "$f" "$outdir/${base}.$newext"
  done
done

#Multi-level Risk Acquisition
##Spices level
conda activate gtdbtk2.4
mkdir -p temp/gtdb_95_226
gtdbtk classify_wf \
  --genome_dir temp/drep95/dereplicated_genomes/ \
  --out_dir temp/gtdb_95_226 \
      --extension fa --skip_ani_screen \
      --prefix tax \
      --cpus 32
python3 scripts/species_summary.py temp/gtdb_95_226/tax.bac120.summary.tsv databases/hpbdb.txt species_level.tsv

##Virulence Leve
conda activate MetaVF_toolkit
python MetaVF_toolkit/metaVF.py \
    -p MetaVF_toolkit \
    -pjn bimrap \
    -id temp/MAG_nucleotide2 \
    -o temp/VF -m draft -c 8 -ti 90 -tc 80
python3 scripts/vf_summary.py temp/VF/bimrap/*/*.summary

##Pathway level
conda activate eggnog
mkdir -p temp/eggnog
tail -n +2 metadataS.txt | cut -f1 | rush -j 4 \
  "emapper.py --itype proteins --data_dir /eggnog \
      -i temp/MAG_protein/{}.fa --cpu 32 -m diamond --override \
      -o temp/eggnog/{}"

mkdir -p temp/eggnog/ko_disease
tail -n +2 metadataS.txt | cut -f1 | rush -j 4 \
    "python3 scripts/genome_ko_table.py temp/eggnog/{}.emapper.annotations databases/KO1-4.txt temp/eggnog/ko_disease/{}.ko.disease -hd"   
python3 scripts/ko_disease_summary.py temp/eggnog/ko_disease/*.ko.disease --sample-mode basename
 
##Resistance level
conda activate deeparg
mkdir -p temp/deeparg
tail -n +2 metadataS.txt | cut -f1 | rush -j 4 \
    "deeparg predict \
        --model LS \
        -i temp/MAG_nucleotide/{1}.fa \
        -o temp/deeparg/{1} \
        -d /home/public/soft/deeparg-data \
        --type nucl \
        --min-prob 0.8 \
        --arg-alignment-identity 90 \
        --arg-alignment-evalue 1e-10 \
        --arg-num-alignments-per-entry 1000"
python3 scripts/arg_summary.py temp/deeparg/*.mapping.ARG 

##Overall risk
python3 overall_risk.py \
  species_level.tsv \
  VF.category.tsv \
  KO.PathwayL2.tsv \
  ARG.type.tsv \
  overall_risk.tsv

python3 scripts/overall_risk_sample.py result/coverm/MAGabundance.tsv overall_risk.tsv overall_risk_sample.tsv



