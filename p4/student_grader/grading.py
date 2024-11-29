"""
This version of the grader is used by students
when completing their assignments. It is very similar to the
master version used by TAs/PMs except that it makes HTTP requests to
our server to get feedback from the LLM, and it uses the metadata
file to inform grader.check about test cases to run
"""

import os
import ast
from typing import List, Dict, Any, Optional
import nbformat
from student_grader.grader_messages import (
    FAILED_FIND_QID_IN_METADATA_FORMAT,
    CHECK_START_FORMAT,
    ISSUES_ABOVE_MSG,
    CUR_QUESTION_ERROR_PREFIX,
    SUCCESS_MSG,
    ABOVE_QUESTION_ERROR_PREFIX,
    MISSED_REQ_FUNC_FORMAT,
    MISSED_REQ_VAR_FORMAT,
    ASSERTION_FAILED_PREFIX,
)
from student_grader.file_loaders import (
    METADATA_FILE_NAME,
    METADATA_REQUIRED_VARS_KEY,
    METADATA_REQUIRED_FUNCS_KEY,
    METADATA_ASSERTIONS_KEY,
    get_nb_path,
    load_metadata_dict,
)
from student_grader.code_execution import execute_code, suppress_output
from student_grader.io_helpers import formatted_print
from student_grader.notebook_layout import (
    CODE_CELL_OFFSET_STUDENT,
    CHECK_CELL_OFFSET_STUDENT,
)

# Describes the starting text expected to be in every points possible markdown cell
# Currently, this is also being used as the key for the possible points for a
# question inside the metadata.pkl file
# SHARED with master_grader
POINTS_POSSIBLE_PREFIX = "Points possible"


def check(
    q_id: str, is_running_from_autograder: bool = False, overwrite_student_nb_path=""
) -> Optional[bool]:
    """
    Executes a series of checks on the student's Jupyter notebook to verify
    that the code for a specific question (identified by `q_id`) is correct.
    This function processes the notebook cells up to the specified check
    cell and validates the student's code against required function calls,
    variable definitions, and assertions.

    Parameters:
        q_id (str): The identifier for the question to check in the notebook, like "q1"
        is_running_from_autograder: Should the function return a boolean True/False
            describing if the check passed or failed? This is useful for the autograder
            but should be disabled for students since otherwise it would print out the
            bool below the check cell. Asking for input will also fail to avoid timing
            out while waiting for input.

    Behavior:
        1. Loads the master notebook and iterates through its cells.
        2. Identifies and processes the cells corresponding to the
           grader check for the given `q_id`.
        3. Executes the student's code and captures global variables and errors.
        4. If an exception occurs while executing the student's code, provides
           immediate feedback.
        5. Validates the student's code for required function calls, variable
           definitions, and failed assertions
        6. Provides feedback on any errors found in the student's code.

    Example:
        To check the code for question 'q1', call:
            student_grader.check("q1")

    Raises:
        FileNotFoundError: If the function cannot find the student notebook file with
            the expected name or it cannot find the assignment metadata
    """

    print(CHECK_START_FORMAT.format(q_id))

    # Load the student notebook
    if overwrite_student_nb_path:
        student_nb_path = overwrite_student_nb_path
    else:
        student_nb_path = get_nb_path()
    with open(student_nb_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)
    dir_path = os.path.dirname(student_nb_path)

    # Load the assignment metadata and check that q_id is present in it
    assignment_metadata = load_metadata_dict(dir_path)
    assert q_id in assignment_metadata, FAILED_FIND_QID_IN_METADATA_FORMAT.format(
        q_id, METADATA_FILE_NAME
    )

    # Store global variables and warnings/errors occuring before curent question
    global_vars = {}
    errors_in_previous_cells = []
    warnings_in_previous_cells = []
    did_check_pass = False

    # Execute the cells up until grader check
    for i, cell in enumerate(notebook.cells[:-CHECK_CELL_OFFSET_STUDENT]):

        found_question_block = cell.source.startswith(POINTS_POSSIBLE_PREFIX)
        found_current_question_block = (
            found_question_block
            and f'student_grader.check("{q_id}")'
            in notebook.cells[i + CHECK_CELL_OFFSET_STUDENT].source
        )

        # Check that all question blocks are properly formatted in the student notebook
        if found_current_question_block:

            # Get text of cells below the points possible cell for the current question block
            student_code = notebook.cells[i + CODE_CELL_OFFSET_STUDENT].source

            # If there are warnings or errors generated by running code in the above
            # cells, alert the student and do not execute the rest of the check.
            if (
                warnings_in_previous_cells or errors_in_previous_cells
            ) and not is_running_from_autograder:
                _print_feedback_student(
                    warnings_in_previous_cells,
                    errors_in_previous_cells,
                )
                print(ISSUES_ABOVE_MSG)
                break

            # Fresh lists for errors and warnings resulting from executing the current question
            current_question_errors = []
            current_question_warnings = []

            # Attempt to execute student's code. If an exception is thrown, stop the
            # check and immediately get feedback so they can fix it before they
            # try to address the test cases
            execute_code(
                student_code,
                global_vars,
                current_question_warnings,
                current_question_errors,
                CUR_QUESTION_ERROR_PREFIX,
            )
            if current_question_errors and not is_running_from_autograder:
                _print_feedback_student(
                    current_question_warnings,
                    current_question_errors,
                )
                break

            required_functions = assignment_metadata[q_id][METADATA_REQUIRED_FUNCS_KEY]
            required_vars = assignment_metadata[q_id][METADATA_REQUIRED_VARS_KEY]
            assertions = assignment_metadata[q_id][METADATA_ASSERTIONS_KEY]
            _check_student_code_against_requirements(
                student_code,
                required_functions,
                required_vars,
                assertions,
                current_question_warnings,
                current_question_errors,
                global_vars,
            )

            # If the student code has any warnings or errors, print out feedback.
            # Otherwise, print out a success message.
            if current_question_warnings or current_question_errors:

                if not is_running_from_autograder:
                    _print_feedback_student(
                        current_question_warnings,
                        current_question_errors,
                    )
            else:
                did_check_pass = True
                print(SUCCESS_MSG)

            # Do not continue executing any other notebook cells after
            # completing check for this q_id
            break

        # If the current cell is a valid code cell not related to the current
        # question, execute it with suppressed output so its output does not appear
        # under the grader.check cell. grader.check
        # cells are skipped in order to avoid recursively calling grader.check
        elif cell.cell_type == "code" and "grader.check" not in cell.source:
            with suppress_output():
                execute_code(
                    cell.source,
                    global_vars,
                    warnings_in_previous_cells,
                    errors_in_previous_cells,
                    ABOVE_QUESTION_ERROR_PREFIX,
                )

    # If the the return mode is selected, return bool if check passed or not
    if is_running_from_autograder:
        return did_check_pass


def _check_student_code_against_requirements(
    student_code: str,
    required_functions: List[str],
    required_vars: List[str],
    assertions: str,
    current_question_warnings: List[str],
    current_question_errors: List[str],
    global_vars: Dict[str, Any],
) -> None:
    """Helper function for packages' grader check functions

    Checks that student code has:
    - used all required functions
    - defined all necessary variables
    - passes all test cases

    and then appends to the list of warnings and/or errors for the
    current question. Used to enforce consistency across all check
    functions in grader packages. SHARED with master_grader.
    """

    for function_name in required_functions:
        if not _does_code_use(student_code, function_name):
            current_question_errors.append(MISSED_REQ_FUNC_FORMAT.format(function_name))

    for required_var in required_vars:
        if required_var not in global_vars:
            current_question_errors.append(MISSED_REQ_VAR_FORMAT.format(required_var))

    execute_code(
        assertions,
        global_vars,
        current_question_warnings,
        current_question_errors,
        ASSERTION_FAILED_PREFIX,
    )


def _print_feedback_student(
    warnings_arr: List[str],
    errors_arr: List[str],
) -> None:
    """Function for printing errors and warnings below grader.check cells

    Grader's interface for getting feedback from the LLM and
    printing out the results. This implementation is different from
    get_llm_feedback_master since it assumes the correct code is not
    provided as an argument.

    Parameters:
        warnings_arr: A list of warning messages
        errors_arr: A list of error messages
        student_code: Code written by the student for the current question
    """

    if warnings_arr:
        formatted_print(warnings_arr, "Warnings:")
    if errors_arr:
        formatted_print(errors_arr, "Errors:")


def _does_code_use(code_snippet: str, name: str) -> bool:
    """Uses ast to tell if code contains a call to a specific function or operator.

    SHARED with master_grader.
    For a list of usable operator names, check
    https://docs.python.org/3/library/ast.html

    Parameters:
        code_snippet: A string containing Python code to be analyzed
        name: The name of the function or ast operator to look for in the code snippet
    """

    class CustomNodeVisitor(ast.NodeVisitor):
        """Extends ast's NoteVisitor to look for functions or operators"""

        def __init__(self):
            self.found = False

        def visit(self, node):
            """Traverse the abstract syntax tree to check for the function call or operator"""

            if isinstance(node, ast.Call):
                full_name = self.get_full_name(node.func)
                if full_name == name:
                    self.found = True
            elif (
                isinstance(node, ast.BinOp)
                or isinstance(node, ast.BoolOp)
                or isinstance(node, ast.UnaryOp)
            ):
                op_name = node.op.__class__.__name__
                if op_name == name:
                    self.found = True
            self.generic_visit(node)

        def get_full_name(self, node):
            """Recursively retrieves the full name of a function being called

            This inclues attribute accesses (e.g., "module.function").
            """

            if isinstance(node, ast.Attribute):
                return self.get_full_name(node.value) + "." + node.attr
            elif isinstance(node, ast.Name):
                return node.id
            return ""

    tree = ast.parse(code_snippet)
    visitor = CustomNodeVisitor()
    visitor.visit(tree)
    return visitor.found
