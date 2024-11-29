"""
Helper functions for executing code. Includes functionality
for suppressing printed output and safely executing code without
modifying global variables or taking too long.
"""

import builtins
import threading
import sys
import os
from typing import List, Dict, Any
from contextlib import contextmanager

# SHARED with master_grader
CODE_MAX_EXECUTION_TIME = 2  # in seconds


def timeout_handler() -> None:
    """Helper function for execute_code to trigger when code has taken too long

    SHARED with master_grader.
    """

    raise RuntimeError(
        "Execution timed out in our grader system. Please modify your code so it runs faster."
    )


def execute_code(
    code: str,
    global_vars: Dict[str, Any],
    warnings_list: List[str],
    errors_list: List[str],
    error_prefix: str,
) -> None:
    """Execute the code and record any warnings or errors.

    Detects and warns about changes to pre-existing global and builtin
    variables when running student code. This helps prevent unintended
    side effects later in the notebook. Uses a timeout to prevent execution
    from lasting too long. SHARED with master_grader.

    Parameters:
        code: Python code to run that potentially contains errors
        global_vars: Dictionary mapping names of global variables to their values
        warnings_list: Records any detected warning messages
        errors_list: Records strings with error_msg and exception text if any occur
        error_prefix: Start of error message to display to the student. Example:
            if desired message is f"Test case failed: {e}", then prefix is "Test case failed: "
    """

    before_exec_globals = global_vars.copy()
    builtin_identifiers = dir(builtins)

    timer = threading.Timer(CODE_MAX_EXECUTION_TIME, timeout_handler)
    timer.start()

    try:
        exec(code, global_vars)
    except Exception as e:
        errors_list.append(f"{error_prefix}{e}")
    finally:
        timer.cancel()  # code finished before alarm went off, cancel the alarm

    after_exec_globals = global_vars.copy()

    for var in before_exec_globals:
        if (
            var in before_exec_globals
            and before_exec_globals[var] != after_exec_globals[var]
        ):
            warnings_list.append(f"Global variable '{var}' was modified.")

    variables_defined_by_exec = set(after_exec_globals) - set(before_exec_globals)
    for var_name in variables_defined_by_exec:
        if var_name in builtin_identifiers:
            warnings_list.append(
                f"Built-in function '{var_name}' was modified. You should never overwrite these."
            )


@contextmanager
def suppress_output():
    """Temporarily suppresses stdout and stderr output.

    Redirects stdout and stderr to os.devnull, effectively silencing
    any print statements or error messages within the context. Once
    the context is exited, the original stdout and stderr are restored.

    This is useful when running executing code in cells above the current
    grader.check call, since we don't want that output to show up
    when the user is expecting information related to the current question.
    SHARED with master_grader.

    Usage:
        with suppress_output():
            # Code with suppressed output
    """
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
