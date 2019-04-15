__author__ = "Adrien Leger"
__copyright__ = "Copyright 2019, Adrien Leger"
__email__ = "aleg@ebi.ac.uk"
__license__ = "MIT"

from snakemake.shell import shell

# Get optional args if unavailable
opt = snakemake.params.get("opt", "")

# Run command
shell("minimap2 -t {snakemake.threads} {opt} -d {snakemake.output[0]} {snakemake.input[0]} &> {snakemake.log}")