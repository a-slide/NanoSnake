# -*- coding: utf-8 -*-

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Imports~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# Std lib
from glob import glob
from os import path

# Third party lib
import pandas as pd
from snakemake.utils import min_version

# set minimum snakemake version
min_version("5.4.2")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Load sample sheets~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

sample_df = pd.read_csv (config["sample_sheet"], comment="#", skip_blank_lines=True, sep="\t", index_col=0)
sample_list = list(sample_df.index)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Create shortcuts~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

merge_fastq_dir = config["merge_fastq"]["outdir"]
fastqc_dir = config["fastqc"]["outdir"]
minimap2_index_dir = config["minimap2_index"]["outdir"]
minimap2_align_dir = config["minimap2_align"]["outdir"]
bamqc_dir = config["bamqc"]["outdir"]
samtools_filter_dir = config["samtools_filter"]["outdir"]
genomecov_dir = config["genomecov"]["outdir"]
nanopolish_dir = config["nanopolish_call_methylation"]["outdir"]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Getters~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def get_fastq (wildcards):
    return glob (sample_df.loc[wildcards.sample, "fastq"])

def get_fast5_dir (wildcards):
    return glob (sample_df.loc[wildcards.sample, "fast5_dir"])

def get_seq_summary (wildcards):
    try:
        return glob (sample_df.loc[wildcards.sample, "seq_summary"])
    except Exception:
        return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Top Rules~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

rule all:
    input:
        expand(path.join("results", merge_fastq_dir,"{sample}.fastq"), sample=sample_list),
        expand(path.join("results", fastqc_dir,"{sample}_fastqc.html"), sample=sample_list),
        expand(path.join("results", fastqc_dir,"{sample}_fastqc.zip"), sample=sample_list),
        expand(path.join("results", minimap2_index_dir,"ref.mmi")),
        expand(path.join("results", minimap2_align_dir, "{sample}.bam"), sample=sample_list),
        expand(path.join("results", bamqc_dir,"{sample}","qualimapReport.html"), sample=sample_list),
        expand(path.join("results", bamqc_dir,"{sample}_samtools_stats.txt"), sample=sample_list),
        expand(path.join("results", bamqc_dir,"{sample}_samtools_flagstat.txt"), sample=sample_list),
        expand(path.join("results", bamqc_dir,"{sample}_samtools_idxstats.txt"), sample=sample_list),
        expand(path.join("results", samtools_filter_dir, "{sample}.bam"), sample=sample_list),
        expand(path.join("results", genomecov_dir,"{sample}.bedgraph"), sample=sample_list),
        expand(path.join("results", merge_fastq_dir,"{sample}.fastq.index"), sample=sample_list),
        expand(path.join("results", merge_fastq_dir,"{sample}.fastq.index.fai"), sample=sample_list),
        expand(path.join("results", merge_fastq_dir,"{sample}.fastq.index.gzi"), sample=sample_list),
        expand(path.join("results", merge_fastq_dir,"{sample}.fastq.index.readdb"), sample=sample_list),
        expand(path.join("results", nanopolish_dir,"{sample}_call_methylation.tsv"), sample=sample_list),
        expand(path.join("results", nanopolish_dir,"{sample}_freq_meth_calculate.bed"), sample=sample_list),
        expand(path.join("results", nanopolish_dir,"{sample}_freq_meth_calculate.tsv"), sample=sample_list),
        expand(path.join("results", nanopolish_dir,"{sample}_freq_meth_calculate.log"), sample=sample_list),

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Rules~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

rule merge_fastq:
    input:
        get_fastq
    output:
        path.join("results", merge_fastq_dir,"{sample}.fastq")
    log:
        path.join("logs", merge_fastq_dir,"{sample}.log")
    wrapper:
        "concat_files"

rule fastqc:
    input:
        rules.merge_fastq.output
    output:
        html=path.join("results", fastqc_dir,"{sample}_fastqc.html"),
        zip=path.join("results", fastqc_dir,"{sample}_fastqc.zip")
    log:
        path.join("logs", fastqc_dir,"{sample}_fastqc.log")
    params:
        opt=config["fastqc"]["opt"]
    threads:
        config["fastqc"]["threads"]
    wrapper:
        "fastqc"

rule minimap2_index:
    input:
        config["reference"]
    output:
        path.join("results", minimap2_index_dir,"ref.mmi")
    log:
        path.join("logs", minimap2_index_dir,"ref.log")
    params:
        opt=config["minimap2_index"]["opt"]
    threads:
        config["minimap2_index"]["threads"]
    wrapper:
        "minimap2_index"

rule minimap2_align:
    input:
        index=rules.minimap2_index.output,
        fastq=rules.merge_fastq.output
    output:
        path.join("results", minimap2_align_dir,"{sample}.bam")
    log:
        path.join("logs", minimap2_align_dir,"{sample}.log")
    params:
        opt=config["minimap2_align"]["opt"],
    threads:
        config["minimap2_align"]["threads"]
    wrapper:
        "minimap2_align"

rule bamqc:
    input:
        rules.minimap2_align.output,
    output:
        qualimap=path.join("results", bamqc_dir,"{sample}","qualimapReport.html"),
        stats=path.join("results", bamqc_dir,"{sample}_samtools_stats.txt"),
        flagstat=path.join("results", bamqc_dir,"{sample}_samtools_flagstat.txt"),
        idxstats=path.join("results", bamqc_dir,"{sample}_samtools_idxstats.txt"),
    log:
        path.join("logs", bamqc_dir,"{sample}.log")
    wrapper:
        "bamqc"

rule samtools_filter:
    input:
        rules.minimap2_align.output
    output:
        path.join("results", samtools_filter_dir,"{sample}.bam")
    log:
        path.join("logs", samtools_filter_dir,"{sample}.log")
    params:
        opt=config["samtools_filter"]["opt"],
    threads:
        config["samtools_filter"]["threads"]
    wrapper:
        "samtools_filter"

rule genomecov:
    input:
        rules.samtools_filter.output
    output:
        path.join("results", genomecov_dir,"{sample}.bedgraph")
    log:
        path.join("logs", genomecov_dir,"{sample}.log")
    params:
        opt=config["genomecov"]["opt"],
    wrapper:
        "genomecov"

rule nanopolish_index:
    input:
        fastq = rules.merge_fastq.output,
        fast5_dir = get_fast5_dir,
        seq_summary = get_seq_summary,
    output:
        index = path.join("results", merge_fastq_dir,"{sample}.fastq.index"),
        fai = path.join("results", merge_fastq_dir,"{sample}.fastq.index.fai"),
        gzi = path.join("results", merge_fastq_dir,"{sample}.fastq.index.gzi"),
        readdb = path.join("results", merge_fastq_dir,"{sample}.fastq.index.readdb"),
    log:
        path.join("logs", merge_fastq_dir,"{sample}_nanopolish_index.log")
    wrapper:
        "nanopolish_index"

rule nanopolish_call_methylation:
    input:
        fastq = rules.merge_fastq.output,
        bam = rules.samtools_filter.output,
        ref = config["reference"],
    output:
        call = path.join("results", nanopolish_dir,"{sample}_call_methylation.tsv"),
        bed = path.join("results", nanopolish_dir,"{sample}_freq_meth_calculate.bed"),
        tsv = path.join("results", nanopolish_dir,"{sample}_freq_meth_calculate.tsv"),
        log = path.join("results", nanopolish_dir,"{sample}_freq_meth_calculate.log"),
    log:
        path.join("logs", nanopolish_dir,"{sample}.log")
    params:
        opt_nanopolish=config["nanopolish_call_methylation"]["opt_nanopolish"],
        opt_nanopolishcomp=config["nanopolish_call_methylation"]["opt_nanopolishcomp"],
    threads:
        config["nanopolish_call_methylation"]["threads"]
    wrapper:
        "nanopolish_call_methylation"

# rule multiqc:
#     input:
#         rules.minimap2_align.output
#     output:
#         path.join("results", samtools_filter_dir,"{sample}.bam")
#     log:
#         path.join("logs", samtools_filter_dir,"{sample}.log")
#     params:
#         opt=config["samtools_filter"]["opt"],
#     threads:
#         config["samtools_filter"]["threads"]
#     wrapper:
#         "multiqc"