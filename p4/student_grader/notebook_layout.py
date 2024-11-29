"""
Variables describing the expected format of each question block in the
student notebook. Shared between student_grader and student_grader_with_feedback.
"""

from typing import Dict

# The following variables describe how many cells below the `Points possible` cell each type
# of cell is located in the master notebook
CODE_CELL_OFFSET_STUDENT = 1
CHECK_CELL_OFFSET_STUDENT = 2

# The following dictionary maps offsets to cell types. This is used in the student notebook
# to help ensure that all of the necessary cells are present before the check runs
OFFSET_TO_TYPE_DICT_STUDENT: Dict[int, str] = {
    CODE_CELL_OFFSET_STUDENT: "code",
    CHECK_CELL_OFFSET_STUDENT: "code",
}
