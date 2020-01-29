__author__ = "Adrien Leger"
__copyright__ = "Copyright 2019, Adrien Leger"
__email__ = "aleg@ebi.ac.uk"
__license__ = "MIT"
__version__ = "0.0.1"

# Imports
from snakemake.shell import shell
import pandas as pd
import os

# Shortcuts
input_counts = snakemake.input.counts
output_counts = snakemake.output.get("counts", None)
output_tpm = snakemake.output.get("tpm", None)

df_counts = pd.DataFrame()
df_tpm = pd.DataFrame()

for c in input_counts:
    sample_id = os.path.basename(c).rpartition(".")[0]
    sample_df = pd.read_csv(c, sep="\t", index_col=0)
    sample_df = sample_df[sample_df["NumReads"] > 0]
    sample_df.dropna(inplace=True)
    sample_df.sort_index(inplace=True)

    # Aggregate counts
    if output_counts:
        counts = sample_df["NumReads"]
        counts.name = sample_id
        df_counts = df_counts.join(counts, how="outer")

    # Calculate and aggregate tpm
    if output_tpm:
        counts = sample_df["TPM"]
        counts.name = sample_id
        df_tpm = df_tpm.join(counts, how="outer")

# Write out
if output_counts:
    df_counts = df_counts.fillna(0)
    df_counts.to_csv(output_counts, sep="\t")
if output_tpm:
    df_tpm = df_tpm.fillna(0)
    df_tpm.to_csv(output_tpm, sep="\t")
