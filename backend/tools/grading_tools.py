import json
import ast
import os
from typing import Dict, Any, Optional, List

from tools.analysis_tools import (
    _is_valid_syntax,
    _extract_elements,
    _check_style,
    _check_documentation,
    _run_test_cases,
)

# ---------------------------------------------------------
# 1. FILE LOADING TOOLS
# ---------------------------------------------------------

def load_rubric(rubric_path: str) -> Dict[str, Any]:
    """Load a grading rubric from a JSON file."""

    ## TEMP: rubric path is currently hard coded, this should be changed
    rubric_path = '/workspaces/Team-H/examples/student_example/rubric.json'
    with open(rubric_path, "r") as f:
        return json.load(f)

def list_repo_files(repo_path: str) -> dict:
    import os
    return {
        "files": os.listdir(repo_path)
    }

def load_submission(submission_path: str) -> str:
    """Load student code from a .py file."""
    print(f"SUB PATH: {submission_path}")
    if not os.path.exists(submission_path):
        raise FileNotFoundError(f"Submission file not found: {submission_path}")

    with open(submission_path, "r") as f:
        code = f.read()

    return code


def load_test_cases(test_cases_path: str) -> Optional[List[Dict[str, Any]]]:
    """Load test cases from a JSON file."""

    ## TEMP: Test cases path is currently hard coded, this should be changed
    test_cases_path = '/workspaces/Team-H/examples/student_example/test_cases.json'
    if not test_cases_path or not os.path.exists(test_cases_path):
        return None
    with open(test_cases_path, "r") as f:
        return json.load(f)


# ---------------------------------------------------------
# 2. ATOMIC CHECKING TOOLS
# ---------------------------------------------------------

def check_syntax(code: str) -> Dict[str, Any]:
    """Check whether the student's code has valid Python syntax."""
    try:
        ast.parse(code)
        return {
            "valid": True,
            "error": None
        }
    except SyntaxError as e:
        return {
            "valid": False,
            "error": str(e)
        }


def check_required_elements(code: str, required_items: List[str]) -> Dict[str, Any]:
    """
    Check whether required functions or classes appear in the code.
    required_items: ["function_name", "ClassName"]
    """
    if not _is_valid_syntax(code):
        return {"found": [], "missing": required_items}

    tree = ast.parse(code)
    found = _extract_elements(tree)

    missing = [r for r in required_items if r not in found]

    return {
        "found": found,
        "missing": missing
    }


def check_documentation_tools(code: str) -> Dict[str, Any]:
    """Check docstrings and comments using your helper scoring."""
    if not _is_valid_syntax(code):
        return {"score": 0.0, "feedback": "Invalid syntax, cannot analyze documentation"}

    tree = ast.parse(code)
    score = _check_documentation(tree, code)

    return {
        "score": score,
        "feedback": (
            "Well documented" if score >= 0.8 else
            "Partial documentation" if score >= 0.5 else
            "Poor documentation"
        )
    }


def check_style_tools(code: str) -> Dict[str, Any]:
    """Check basic style using your scoring system."""
    score = _check_style(code)
    return {
        "score": score,
        "feedback": (
            "Good style" if score >= 0.8 else
            "Could improve style"
        )
    }


def run_functional_tests(code: str, test_cases: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Run functional test cases against the student's code."""
    if not test_cases:
        return {
            "passed": 0,
            "total": 0,
            "feedback": ["No test cases provided."]
        }

    passed, total, feedback = _run_test_cases(code, test_cases)

    return {
        "passed": passed,
        "total": total,
        "feedback": feedback
    }


# ---------------------------------------------------------
# 3. AGGREGATION TOOL (FINAL GRADE)
# ---------------------------------------------------------

def compute_final_grade(
    rubric: Dict[str, Any],
    syntax: Dict[str, Any],
    required: Dict[str, Any],
    documentation: Dict[str, Any],
    style: Dict[str, Any],
    tests: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Combine all partial results into a rubric-based final grade.
    This is the final "reduce" step after all atomic tools have been run.
    """

    results = {
        "breakdown": {},
        "total_score": 0,
        "max_score": 0,
        "percentage": 0,
    }

    # 1. Syntax
    if "syntax" in rubric:
        pts = rubric["syntax"]["points"]
        results["max_score"] += pts

        earned = pts if syntax["valid"] else 0
        results["breakdown"]["syntax"] = {
            "earned": earned,
            "possible": pts,
            "feedback": ["✓ Valid syntax"] if syntax["valid"] else [f"✗ Syntax error: {syntax['error']}"]
        }
        results["total_score"] += earned

    # 2. Required elements
    if "required_elements" in rubric:
        pts = rubric["required_elements"]["points"]
        results["max_score"] += pts

        required_items = rubric["required_elements"]["items"]
        per_item = pts / len(required_items) if required_items else 0

        earned = per_item * (len(required_items) - len(required["missing"]))

        feedback = []
        for item in required_items:
            if item in required["found"]:
                feedback.append(f"✓ Found: {item}")
            else:
                feedback.append(f"✗ Missing: {item}")

        results["breakdown"]["required_elements"] = {
            "earned": earned,
            "possible": pts,
            "feedback": feedback
        }
        results["total_score"] += earned

    # 3. Documentation
    if "documentation" in rubric:
        pts = rubric["documentation"]["points"]
        results["max_score"] += pts

        earned = pts * documentation["score"]

        results["breakdown"]["documentation"] = {
            "earned": earned,
            "possible": pts,
            "feedback": [documentation["feedback"]]
        }
        results["total_score"] += earned

    # 4. Style
    if "style" in rubric:
        pts = rubric["style"]["points"]
        results["max_score"] += pts

        earned = pts * style["score"]

        results["breakdown"]["style"] = {
            "earned": earned,
            "possible": pts,
            "feedback": [style["feedback"]]
        }
        results["total_score"] += earned

    # 5. Test Cases
    if "functionality" in rubric and tests["total"] > 0:
        pts = rubric["functionality"]["points"]
        results["max_score"] += pts

        pass_ratio = tests["passed"] / tests["total"]
        earned = pts * pass_ratio

        results["breakdown"]["functionality"] = {
            "earned": earned,
            "possible": pts,
            "feedback": [f"Passed {tests['passed']} / {tests['total']} tests"] + tests["feedback"]
        }
        results["total_score"] += earned

    # Recalculate total score from the breakdown to avoid double-counting and keep a single source of truth
    results["total_score"] = 0
    for category in results["breakdown"].values():
        results["total_score"] += category["earned"]

    # Round scores
    results["total_score"] = round(results["total_score"], 2)
    for category in results["breakdown"].values():
        category["earned"] = round(category["earned"], 2)

    # Generate overall feedback
    percentage = (results["total_score"] / results["max_score"] * 100) if results["max_score"] > 0 else 0
    results["percentage"] = round(percentage, 1)

    # Human-friendly summary for frontend display
    title = rubric.get("title") or rubric.get("name") or "Assignment"
    if results["max_score"] > 0:
        summary = f"{title}: {results['total_score']} / {round(results['max_score'],2)} pts ({results['percentage']}%)"
    else:
        summary = f"{title}: No graded items"

    # If functionality existed in the rubric but there were no test cases, add a short note
    if "functionality" in rubric and tests.get("total", 0) == 0:
        summary += " — Functionality tests were skipped (no test cases provided)."

    results["summary"] = summary

    return results
