"""Module containing the CLI's core logic."""

import sys
import os
from datetime import datetime
from .args_handler import handle_cli_args
from engine.preprocessing.module_parser import get_modules_from_dir
from engine.algorithms.algorithm_runner import run_two_repos
from engine.utils.benchmark import time_snap
from fastlog import log
from engine.errors.user_input import UserInputError


def main():
    """Entry point of the application."""
    try:
        # Parse command line arguments
        repos, algorithm = handle_cli_args()

        time_snap("Cloned repositories")

        # Find all functions and parse their syntax tree using the TreeNode wrapper
        log.info("Parsing methods in repositories...")
        module_list_1 = get_modules_from_dir(repos[0])

        if not module_list_1:
            raise UserInputError(f"First repository is empty: \"{repos[0]}\"")

        time_snap("Parsed first repository")

        module_list_2 = get_modules_from_dir(repos[1])

        if not module_list_2:
            raise UserInputError(f"Second repository is empty: \"{repos[1]}\"")

        time_snap("Parsed second repository")

        log.info("Beginning full analysis...")
        clones = run_two_repos(module_list_1, module_list_2, algorithm)
        time_snap("Analysis completed")

        # Create output directory if it doesn't exist and print output
        output_path = os.getcwd()
        output_filename = "clones_" + \
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
        os.makedirs(output_path, exist_ok=True)
        with open(os.path.join(output_path, output_filename), "w") as output_file:
            output_file.write(clones.json())

    except UserInputError as ex:
        if ex.message:
            log.error(ex.message)

        sys.exit(ex.code)
