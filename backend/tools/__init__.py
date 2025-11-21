"""Tools package initialization."""

# Public tools
from tools.testing_tools import (
    run_pytest_on_directory,
)

from tools.grading_tools import (
    load_rubric,
    load_submission,
    list_repo_files,
    load_test_cases,
    check_syntax,
    check_required_elements,
    check_documentation_tools,
    check_style_tools,
    run_functional_tests,
    compute_final_grade,
)

__all__ = [
    # Atomic grading tools
    "load_rubric",
    "load_submission",
    "list_repo_files",
    "load_test_cases",
    "check_syntax",
    "check_required_elements",
    "check_documentation_tools",
    "check_style_tools",
    "run_functional_tests",
    "compute_final_grade",

    # Test-running tool
    "run_pytest_on_directory",
]
