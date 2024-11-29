"""
Helper functions for loading files, including the master notebook
file and the dictionary from the metadata.pkl file.
"""

import os
import re
import pickle
from typing import Dict, Any, Optional

# The name for the metadata file for each assignment containing required vars/funcs and assertions
# SHARED with master_grader
METADATA_FILE_NAME = "metadata.pkl"

# Keys to use in the assignment metadata dictionary
# These three vars are SHARED with master_grader
METADATA_REQUIRED_VARS_KEY = "required_vars"
METADATA_REQUIRED_FUNCS_KEY = "required_funcs"
METADATA_ASSERTIONS_KEY = "assertions"

NB_FILE_PATH = None
NB_DIR_PATH = None


class InitializationError(Exception):
    """Custom exception raised when functions are called out of sequence.

    SHARED with master_grader.
    """

    def __init__(
        self,
        message=(
            "You must initialize before accessing this path. "
            "Please run the import cell at the top of the notebook "
            "before continuing."
        ),
    ):
        self.message = message
        super().__init__(self.message)


class PathNotFoundError(Exception):
    """Custom exception raised when a directory does not exist.

    SHARED with master_grader.
    """

    def __init__(self, message="Tried to access a path that does not exist"):
        self.message = message
        super().__init__(self.message)


def initialize(nb_dir_path: str, project_name: str) -> None:
    """Called by the first cell within the student .ipynb file

    Tells the student_grader package the location of the .ipynb
    file loading the package. Without this functionality, the
    `check` function would not know where to look for the
    notebook file before executing its cells.
    SHARED with master_grader.
    """

    if not os.path.exists(nb_dir_path):
        raise PathNotFoundError(f"{nb_dir_path} does not exist")

    global NB_FILE_PATH, NB_DIR_PATH
    NB_DIR_PATH = nb_dir_path

    NB_FILE_PATH = os.path.join(nb_dir_path, f"{project_name}.ipynb")

    if not os.path.exists(NB_FILE_PATH):
        raise FileNotFoundError(
            (
                f"We expected your notebook to be at {NB_FILE_PATH}, "
                "but it's not there. Please do not change the name of "
                "the notebook file after extracting the assignment zip file."
            )
        )


def get_nb_path() -> str:
    """Return the full path of the .ipynb file importing the grader package

    Raises an error if the initialize function was not
    previously called. SHARED with master_grader.
    """

    if NB_FILE_PATH is None:
        raise InitializationError()
    return NB_FILE_PATH


def load_metadata_dict(overwrite_dir_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads the assignment's metadata from the .pkl file

    A .pkl file is used to make it harder for students to
    view the contents of the file. This file is used by the
    student_grader and also by the autograder to determine
    which tests to run for each question.
    SHARED with master_grader.

    Parameters:
        overwrite_dir_path: Optional way to specify the path to
            the directory containing the .pkl file without needing
            to call initialize. This is useful for the autograder.

    Returns:
        assignment_metadata: Dictionary mapping question identifiers to information
            about that question, such as how many points it's worth or what test
            cases need to be run for it
    """

    global NB_DIR_PATH

    if NB_DIR_PATH is None and overwrite_dir_path is None:
        raise InitializationError()

    if overwrite_dir_path is not None:
        metadata_file_path = os.path.join(overwrite_dir_path, METADATA_FILE_NAME)
    else:
        metadata_file_path = os.path.join(NB_DIR_PATH, METADATA_FILE_NAME)

    if not os.path.isfile(metadata_file_path):
        raise FileNotFoundError(
            (
                f"Could not find {METADATA_FILE_NAME} at {metadata_file_path}."
                "Please do not delete or rename the metadata file included"
                "in the assignment zip. Please re-download the assignment"
                "zip file if you need to recover this file."
            )
        )

    with open(metadata_file_path, "rb") as file:
        assignment_metadata = pickle.load(file)

    return assignment_metadata
