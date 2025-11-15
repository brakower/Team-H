"""Tools package initialization."""

# Public tools
from backend.tools.example_tools import (
    calculator,
    string_analyzer,
    list_processor,
    json_formatter,
)

from backend.tools.testing_tools import (
    run_pytest_on_directory,
)

from backend.tools.grading_tools import (
    load_rubric,
    load_submission,
    load_test_cases,
    check_syntax,
    check_required_elements,
    check_documentation_tools,
    check_style_tools,
    run_functional_tests,
    compute_final_grade,
)

__all__ = [
    # Core example tools
    "calculator",
    "string_analyzer",
    "list_processor",
    "json_formatter",

    # Atomic grading tools
    "load_rubric",
    "load_submission",
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
