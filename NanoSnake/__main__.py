#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~IMPORTS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Standard library imports
import os
import sys
import argparse
import pkg_resources
import shutil
from collections import *
import inspect
import yaml

# Third party library
from snakemake import snakemake
import pandas as pd

# Local imports
from NanoSnake import __version__ as package_version
from NanoSnake import __name__ as package_name
from NanoSnake import __description__ as package_description
from NanoSnake.common import *

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~LOGGING INFO~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(package_name)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~GLOBAL DIRS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
WRAPPER_DIR = pkg_resources.resource_filename (package_name, "wrappers")
WORKFLOW_DIR = pkg_resources.resource_filename (package_name, "workflows")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~CLI ENTRY POINT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def main(args=None):
    """
    Main entry point for NanoSnake command line interface
    """

    # Parser and subparsers for command
    parser = argparse.ArgumentParser (description=package_description)
    parser.add_argument("--version", action="version", version="{} v{}".format(package_name, package_version))
    subparsers = parser.add_subparsers (description="%(prog)s implements the following subcommands", dest="subcommands")
    subparsers.required = True

    # DNA subparser
    subparser_dna = subparsers.add_parser("DNA", description="Workflow for DNA Analysis of Nanopore data")
    subparser_dna.set_defaults(func=DNA)
    subparser_dna_IO = subparser_dna.add_argument_group("input/output options")
    subparser_dna_IO.add_argument("--reference", "-r", default=None, type=str, help="Path to a Fasta reference file to be used for read mapping (required)")
    subparser_dna_IO.add_argument("--sample_sheet", "-s", default=None, type=str, help="Path to a tabulated sample sheet (required)")

    # RNA subparser
    subparser_rna = subparsers.add_parser("RNA", description="Workflow for RNA Analysis of Nanopore data")
    subparser_rna.set_defaults(func=RNA)

    # Add common group parsers
    for sp in [subparser_dna, subparser_rna]:
        sp_IO = add_argument_group (sp, "input/output options")
        sp_IO.add_argument("--config", "-c", default=None, type=str, help="Snakemake configuration YAML file. Provide a cluster_config file instead if using cluster support (required)")
        sp_IO.add_argument("--workdir", "-d", default="./", type=str, help="Path to the working dir where to deploy the workflow (default: %(default)s)")
        sp_template = add_argument_group (sp, "Template options")
        sp_template.add_argument("--generate_template", "-g", type=str, nargs="+", default=[], choices=["all", "sample_sheet", "config", "multiqc_config", "cluster_config"], help="Generate template files (configs + sample_sheet) in workdir and exit (default: %(default)s)")
        sp_template.add_argument("--overwrite_template", "-o", action="store_true", default=False, help="Overwrite existing template files if they already exist (default: %(default)s).")
        sp_verbosity = sp.add_mutually_exclusive_group()
        sp_verbosity.add_argument("--verbose", "-v", action="store_true", default=False, help="Show additional debug output (default: %(default)s)")
        sp_verbosity.add_argument("--quiet", "-q", action="store_true", default=False, help="Reduce overall output (default: %(default)s)")
        sp_snakemake = add_argument_group(sp, "Snakemake options")
        sp_snakemake.add_argument("--report", type=str, default=None, help="create an HTML report for a previous run at the given path (default: %(default)s)")
        sp_snakemake.add_argument("--listrules", action="store_true", default=False, help="list rules (default: %(default)s)")
        sp_snakemake.add_argument("--list_target_rules", action="store_true", default=False, help="list target rules (default: %(default)s)")
        sp_snakemake.add_argument("--cores", "-j", type=int, default=1, help="the number of provided cores (default: %(default)s)")
        sp_snakemake.add_argument("--nodes", type=int, default=1, help="the number of provided cluster nodes (ignored without cluster support) (default: %(default)s)")
        sp_snakemake.add_argument("--targets", type=str, nargs='+', default=[], help="list of targets, e.g. rule or file names (default: %(default)s)")
        sp_snakemake.add_argument("--dryrun", action="store_true", default=False, help="only dry-run the workflow (default: %(default)s)")
        sp_snakemake.add_argument("--touch", action="store_true", default=False, help="only touch all output files if present (default: %(default)s)")
        sp_snakemake.add_argument("--forcetargets", action="store_true", default=False, help="force given targets to be re-created (default: %(default)s)")
        sp_snakemake.add_argument("--forceall", action="store_true", default=False, help="force all output files to be re-created (default: %(default)s)")
        sp_snakemake.add_argument("--forcerun", type=str, nargs='+', default=[], help="list of files and rules that shall be re-created/re-executed (default: %(default)s)")
        sp_snakemake.add_argument("--prioritytargets", type=str, nargs='+', default=[], help="list of targets that shall be run with maximum priority (default: %(default)s)")
        sp_snakemake.add_argument("--stats", type=str, default=None, help="path to file that shall contain stats about the workflow execution (default: %(default)s)")
        sp_snakemake.add_argument("--printreason", action="store_true", default=False, help="print the reason for the execution of each job (default: %(default)s)")
        sp_snakemake.add_argument("--printshellcmds", action="store_true", default=False, help="print the shell command of each job (default: %(default)s)")
        sp_snakemake.add_argument("--printdag", action="store_true", default=False, help="print the dag in the graphviz dot language (default: %(default)s)")
        sp_snakemake.add_argument("--printrulegraph", action="store_true", default=False, help="print the graph of rules in the graphviz dot language (default: %(default)s)")
        sp_snakemake.add_argument("--printd3dag", action="store_true", default=False, help="print a D3.js compatible JSON representation of the DAG (default: %(default)s)")
        sp_snakemake.add_argument("--nocolor", action="store_true", default=False, help="do not print colored output (default: %(default)s)")
        sp_snakemake.add_argument("--keepgoing", action="store_true", default=False, help="keep goind upon errors (default: %(default)s)")
        sp_snakemake.add_argument("--cluster", type=str, default=None, help="submission command of a cluster or batch system to use, e.g. qsub (default: %(default)s)")
        sp_snakemake.add_argument("--drmaa_log_dir", type=str, default=None, help="the path to stdout and stderr output of DRMAA jobs (default: %(default)s)")
        sp_snakemake.add_argument("--jobname", type=str, default='snakejob.{rulename}.{jobid}.sh', help="naming scheme for cluster job scripts (default: %(default)s)")
        sp_snakemake.add_argument("--immediate_submit", action="store_true", default=False, help="immediately submit all cluster jobs, regardless of dependencies (default: %(default)s)")
        sp_snakemake.add_argument("--ignore_ambiguity", action="store_true", default=False, help="ignore ambiguous rules and always take the first possible one (default: %(default)s)")
        sp_snakemake.add_argument("--unlock", action="store_true", default=False, help="just unlock the working directory (default: %(default)s)")
        sp_snakemake.add_argument("--cleanup_metadata", type=str, nargs='+', default=[], help="just cleanup metadata of given list of output files (default: %(default)s)")
        sp_snakemake.add_argument("--cleanup_conda", action="store_true", default=False, help="just cleanup unused conda environments (default: %(default)s)")
        sp_snakemake.add_argument("--force_incomplete", action="store_true", default=False, help="force the re-creation of incomplete files (default: %(default)s)")
        sp_snakemake.add_argument("--ignore_incomplete", action="store_true", default=False, help="ignore incomplete files (default: %(default)s)")
        sp_snakemake.add_argument("--archive", type=str, default=None, help="archive workflow into the given tarball (default: %(default)s)")
        sp_snakemake.add_argument("--delete_all_output", action="store_true", default=False, help="remove all files generated by the workflow (default: %(default)s)")
        sp_snakemake.add_argument("--delete_temp_output", action="store_true", default=False, help="remove all temporary files generated by the workflow (default: %(default)s)")
        sp_snakemake.add_argument("--latency_wait", type=int, default=3, help="how many seconds to wait for an output file to appear after the execution of a job, e.g. to handle filesystem latency (default: %(default)s)")
        sp_snakemake.add_argument("--wait_for_files", type=str, nargs='+', default=[], help="wait for given files to be present before executing the workflow (default: %(default)s)")
        sp_snakemake.add_argument("--list_resources", action="store_true", default=False, help="list resources used in the workflow (default: %(default)s)")
        sp_snakemake.add_argument("--summary", action="store_true", default=False, help="list summary of all output files and their status. If no option is specified a basic summary will be ouput. If ‘detailed’ is added as an option e.g –summary detailed, extra info about the input and shell commands will be included (default: %(default)s)")
        sp_snakemake.add_argument("--detailed_summary", action="store_true", default=False, help="list summary of all input and output files and their status (default: %(default)s)")
        sp_snakemake.add_argument("--print_compilation", action="store_true", default=False, help="print the compilation of the snakefile (default: %(default)s)")
        sp_snakemake.add_argument("--debug", action="store_true", default=False, help="allow to use the debugger within rules (default: %(default)s)")
        sp_snakemake.add_argument("--notemp", action="store_true", default=False, help="ignore temp file flags, e.g. do not delete output files marked as temp after use (default: %(default)s)")
        sp_snakemake.add_argument("--keep_remote_local", action="store_true", default=False, help="keep local copies of remote files (default: %(default)s)")
        sp_snakemake.add_argument("--nodeps", action="store_true", default=False, help="ignore dependencies (default: %(default)s)")
        sp_snakemake.add_argument("--keep_target_files", action="store_true", default=False, help="do not adjust the paths of given target files relative to the working directory. (default: %(default)s)")
        sp_snakemake.add_argument("--overwrite_shellcmd", type=str, default=None, help="a shell command that shall be executed instead of those given in the workflow. This is for debugging purposes only (default: %(default)s)")
        sp_snakemake.add_argument("--updated_files", type=str, nargs='+', default=[], help="a list that will be filled with the files that are updated or created during the workflow execution (default: %(default)s)")
        sp_snakemake.add_argument("--max_jobs_per_second", type=int, default=None, help="maximal number of cluster/drmaa jobs per second, None to impose no limit (default: %(default)s)")
        sp_snakemake.add_argument("--restart_times", type=int, default=0, help="number of times to restart failing jobs (default: %(default)s)")
        sp_snakemake.add_argument("--attempt", type=int, default=1, help="initial value of Job.attempt. This is intended for internal use only (default: %(default)s)")
        sp_snakemake.add_argument("--force_use_threads", action="store_true", default=False, help="whether to force use of threads over processes. helpful if shared memory is full or unavailable (default: %(default)s)")
        sp_snakemake.add_argument("--conda_prefix", type=str, default=None, help="the directory in which conda environments will be created (default: %(default)s)")
        sp_snakemake.add_argument("--create_envs_only", action="store_true", default=False, help="if specified, only builds the conda environments specified for each job, then exits. (default: %(default)s)")
        sp_snakemake.add_argument("--list_conda_envs", action="store_true", default=False, help="list conda environments and their location on disk. (default: %(default)s)")
#        sp_snakemake.add_argument("--use_singularity", action="store_true", default=False, help="run jobs in singularity containers (if defined with singularity directive) (default: %(default)s)")
#        sp_snakemake.add_argument("--singularity_args", type=str, default=None, help="additional arguments to pass to singularity (default: %(default)s)")
#        sp_snakemake.add_argument("--singularity_prefix", type=str, default=None, help="the directory to which singularity images will be pulled (default: %(default)s)")
#        sp_snakemake.add_argument("--drmaa", type=str, default=None, help="if not None use DRMAA for cluster support, str specifies native args passed to the cluster when submitting a job (default: %(default)s)")
#        sp_snakemake.add_argument("--cluster_sync", type=str, default=None, help="blocking cluster submission command (like SGE ‘qsub -sync y’) (default: %(default)s)")
#        sp_snakemake.add_argument("--cleanup_shadow", action="store_true", default=False, help="just cleanup old shadow directories (default: %(default)s)")
#        sp_snakemake.add_argument("--list_version_changes", action="store_true", default=False, help="list output files with changed rule version (default: %(default)s)")
#        sp_snakemake.add_argument("--list_code_changes", action="store_true", default=False, help="list output files with changed rule code (default: %(default)s)")
#        sp_snakemake.add_argument("--list_input_changes", action="store_true", default=False, help="list output files with changed input files (default: %(default)s)")
#        sp_snakemake.add_argument("--list_params_changes", action="store_true", default=False, help="list output files with changed params (default: %(default)s)")
#        sp_snakemake.add_argument("--list_untracked", action="store_true", default=False, help="list files in the workdir that are not used in the workflow (default: %(default)s)")
#        sp_snakemake.add_argument("--jobscript", type=str, default=None, help="path to a custom shell script template for cluster jobs (default: %(default)s)")
#        sp_snakemake.add_argument("--shadow_prefix", type=str, default=None, help="prefix for shadow directories. The job-specific shadow directories will be created in $SHADOW_PREFIX/shadow/ (default: %(default)s)")
#        sp_snakemake.add_argument("--kubernetes", type=str, default=None, help="submit jobs to kubernetes, using the given namespace. (default: %(default)s)")
#        sp_snakemake.add_argument("--kubernetes_envvars", type=str, nargs='+', default=[], help="environment variables that shall be passed to kubernetes jobs. (default: %(default)s)")
#        sp_snakemake.add_argument("--container_image", type=str, default=None, help="Docker image to use, e.g., for kubernetes. (default: %(default)s)")
#        sp_snakemake.add_argument("--default_remote_provider", type=str, default=None, help="default remote provider to use instead of local files (e.g. S3, GS) (default: %(default)s)")
#        sp_snakemake.add_argument("--default_remote_prefix", type=str, default=None, help="prefix for default remote provider (e.g. name of the bucket). (default: %(default)s)")
#        sp_snakemake.add_argument("--cluster_status", type=str, default=None, help="status command for cluster execution. If None, Snakemake will rely on flag files. Otherwise, it expects the command to return “success”, “failure” or “running” when executing with a cluster jobid as single argument. (default: %(default)s)")
#        sp_snakemake.add_argument("--export_cwl", type=str, default=None, help="Compile workflow to CWL and save to given file (default: %(default)s)")

    # Parse args and call subfunction
    args = parser.parse_args()

    # Change overall verbose level if verbose or quiet
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)

    # Generate template if required
    if args.generate_template:
        logger.warning (f"Generate template files in working directory")
        generate_template (templates=args.generate_template, workflow=args.subcommands, outdir=args.workdir, overwrite=args.overwrite_template)
        sys.exit()

    # Cluster stuff to simplify options
    if args.cluster:
        logger.warning (f"INITIALISING WORKFLOW IN CLUSTER MODE")
        args.local_cores = args.cores
        args.cluster_config = args.config
    else:
        logger.warning (f"INITIALISING WORKFLOW IN LOCAL MODE")

    # Run workflow
    args.func(args)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~SUBPARSERS FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def DNA (args):
    """"""
    # Get and check config files
    logger.warning ("CHECKING CONFIGURATION FILES")
    snakefile = os.path.join (WORKFLOW_DIR, "DNA", "snakefile.py")
    configfile = get_config_fn (config=args.config)

    ###### To be changed depending on optional steps ###### To be changed depending on optional steps ###### To be changed depending on optional steps
    sample_sheet = get_sample_sheet (sample_sheet=args.sample_sheet, required_fields=["sample_id", "fastq", "fast5", "seq_summary"])
    reference = get_reference (args.reference)

    # Store additionnal options to pass to snakemake
    logger.info ("Build config dict for snakemake")
    extra_config = {"reference": reference,"sample_sheet": sample_sheet}
    logger.debug (extra_config)

    # Filter other args option compatible with snakemake API
    kwargs = filter_valid_snakemake_options (args)
    logger.debug (kwargs)

    # Run Snakemake through the API
    logger.warning ("RUNING SNAKEMAKE PIPELINE")
    snakemake (
        snakefile=snakefile,
        configfile=configfile,
        config=extra_config,
        use_conda=True,
        wrapper_prefix=f"file:{WRAPPER_DIR}/",
        **kwargs)

def RNA (args):
    """"""
    pass

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~HELPER FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def add_argument_group (parser, title):
    """Add group only is it doesn't exist yet"""
    for group in parser._action_groups:
        if group.title == title:
            return group
    return parser.add_argument_group(title)

def filter_valid_snakemake_options (args):
    """Filter out options that are not in the snakemake API"""
    valid_options = list(inspect.signature(snakemake).parameters.keys())
    valid_kwargs = OrderedDict()
    for k,v in vars(args).items():
        if k in valid_options and k != "config":
            valid_kwargs[k] = v
    return valid_kwargs

def generate_template (templates, workflow, outdir="./", overwrite=False):
    """"""
    templates_to_fname = {
        "sample_sheet":"sample_sheet.tsv" ,
        "config":"config.yaml",
        "multiqc_config":"multiqc_config.yaml",
        "cluster_config":"cluster_config.yaml"}

    for template, fname in templates_to_fname.items():
        if template in templates or "all" in templates:

            # Create src path and test readability
            src_fn = os.path.join (WORKFLOW_DIR, workflow, "templates", fname)
            if not access_file(src_fn):
                logger.warning (f"\tTemplate file {src_fn} doesnt exist for workflow {workflow}")
                continue

            # Create destination file name and test if it exists
            dest_fn = os.path.join(outdir, fname)
            if os.path.isfile(dest_fn) and not overwrite:
                logger.warning (f"\tTemplate file {dest_fn} already exists in working directory. Use --overwrite_template to replace the existing file")
                continue

            # Write scr in dest
            logger.warning (f"\tCreate template file {dest_fn}")
            shutil.copy2 (src_fn, dest_fn)

def get_config_fn (config):
    """"""
    # Try loading the config file
    try:
        with open(config) as fp:
            yaml.load(fp, Loader=yaml.FullLoader)
    except:
        raise NanoSnakeError (f"The provided config file ({config}) is not readeable or not a valid yaml file")

    return config

def get_sample_sheet (sample_sheet, required_fields=[]):
    """"""
    if not sample_sheet:
        raise NanoSnakeError ("A sample_sheet file (--sample_sheet) is required to run the workflow")
    try:
        sample_df = pd.read_csv (sample_sheet, comment="#", skip_blank_lines=True, sep="\t")
    except:
        raise NanoSnakeError ()
    for f in required_fields:
        if not f in sample_df.columns:
            raise NanoSnakeError ()
    logger.warning ("\tValid sample sheet")
    return sample_sheet

def get_reference (reference):
    """"""
    if not reference:
        raise NanoSnakeError ("A reference file (--reference) is required to run the workflow")
    if not access_file(reference):
        raise NanoSnakeError (f"The reference file {reference} is not readeable")
    logger.warning ("\tValid reference file")
    return reference

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~SCRIPT ENTRY POINT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

if __name__ == "__main__":
    main ()
