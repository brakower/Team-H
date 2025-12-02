import asyncio
import json
import ast
import os
import time
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

def load_rubric(rubric: Optional[Dict[str, Any]] = None, rubric_path: Optional[str] = None, selected_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Load a grading rubric.

    This function supports two modes:
    - `rubric_path` (str): load a JSON file from disk (legacy behavior)
    - `rubric` (dict): use a rubric JSON object uploaded by the frontend

    If `rubric` is provided in the uploaded form used by the frontend (contains
    a top-level `rubric_items` list), this function will convert that list into
    a mapping keyed by item id. If `selected_ids` is provided, only those items
    will be returned.
    """

    data = None
    # 1) Prefer an in-memory rubric dict if provided
    if rubric is not None:
        data = rubric
    # 2) Fall back to loading from a path if provided
    elif rubric_path:
        if not os.path.exists(rubric_path):
            raise FileNotFoundError(f"Rubric file not found: {rubric_path}")
        with open(rubric_path, "r") as f:
            data = json.load(f)
    else:
        raise ValueError("Either `rubric` (dict) or `rubric_path` (str) must be provided")

    # If the uploaded rubric follows the frontend schema (RubricSchema), it will
    # contain `rubric_items` as a list of items with id/label/description/max_points
    if isinstance(data, dict) and "rubric_items" in data:
        out: Dict[str, Any] = {}
        for item in data["rubric_items"]:
            item_id = item.get("id")
            if not item_id:
                continue
            if selected_ids and item_id not in selected_ids:
                continue
            entry: Dict[str, Any] = {
                "points": item.get("max_points", item.get("points", 0)),
                "description": item.get("description", ""),
            }
            if item.get("items") is not None:
                entry["items"] = item.get("items")
            out[item_id] = entry
        return out

    # If data is already a mapping of categories -> config, optionally filter keys
    if isinstance(data, dict):
        if selected_ids:
            return {k: v for k, v in data.items() if k in selected_ids}
        return data

    # Unknown format
    raise ValueError("Unsupported rubric format")

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
    syntax: Optional[Dict[str, Any]] = None,
    required: Optional[Dict[str, Any]] = None,
    documentation: Optional[Dict[str, Any]] = None,
    style: Optional[Dict[str, Any]] = None,
    tests: Optional[Dict[str, Any]] = None,
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

    # 1. Syntax — only compute if syntax is present in rubric
    if "syntax" in rubric:
        pts = rubric["syntax"].get("points", rubric["syntax"].get("max_points", 0))
        results["max_score"] += pts

        if syntax and syntax.get("valid"):
            earned = pts
            feedback = ["✓ Valid syntax"]
        else:
            earned = 0
            feedback = [f"✗ Syntax error: {syntax.get('error')}" ] if syntax and syntax.get("error") else ["✗ Syntax check failed or not run"]

        results["breakdown"]["syntax"] = {
            "earned": earned,
            "possible": pts,
            "feedback": feedback,
        }
        results["total_score"] += earned

    # 2. Required elements
    if "required_elements" in rubric:
        pts = rubric["required_elements"].get("points", rubric["required_elements"].get("max_points", 0))
        results["max_score"] += pts

        required_items = rubric["required_elements"].get("items", [])
        per_item = pts / len(required_items) if required_items else 0

        if required:
            earned = per_item * (len(required_items) - len(required.get("missing", [])))
        else:
            # if required check wasn't run, treat as 0 earned
            earned = 0

        feedback = []
        for item in required_items:
            if required and item in required.get("found", []):
                feedback.append(f"✓ Found: {item}")
            else:
                feedback.append(f"✗ Missing: {item}")

        results["breakdown"]["required_elements"] = {
            "earned": earned,
            "possible": pts,
            "feedback": feedback,
        }
        results["total_score"] += earned

    # 3. Documentation
    if "documentation" in rubric:
        pts = rubric["documentation"].get("points", rubric["documentation"].get("max_points", 0))
        results["max_score"] += pts

        if documentation and "score" in documentation:
            earned = pts * documentation.get("score", 0)
            feedback = [documentation.get("feedback", "")] if documentation.get("feedback") else []
        else:
            earned = 0
            feedback = ["Documentation check skipped or not run"]

        results["breakdown"]["documentation"] = {
            "earned": earned,
            "possible": pts,
            "feedback": feedback,
        }
        results["total_score"] += earned

    # 4. Style
    if "style" in rubric:
        pts = rubric["style"].get("points", rubric["style"].get("max_points", 0))
        results["max_score"] += pts

        if style and "score" in style:
            earned = pts * style.get("score", 0)
            feedback = [style.get("feedback", "")] if style.get("feedback") else []
        else:
            earned = 0
            feedback = ["Style check skipped or not run"]

        results["breakdown"]["style"] = {
            "earned": earned,
            "possible": pts,
            "feedback": feedback,
        }
        results["total_score"] += earned

    # 5. Test Cases / Functionality
    if "functionality" in rubric and tests and tests.get("total", 0) > 0:
        pts = rubric["functionality"].get("points", rubric["functionality"].get("max_points", 0))
        results["max_score"] += pts

        pass_ratio = tests.get("passed", 0) / tests.get("total", 1)
        earned = pts * pass_ratio

        results["breakdown"]["functionality"] = {
            "earned": earned,
            "possible": pts,
            "feedback": [f"Passed {tests.get('passed',0)} / {tests.get('total',0)} tests"] + tests.get("feedback", []),
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


# ---------------------------------------------------------
# 3. Grade Rubric Items TOOL (Multi Agent Framework)
# ---------------------------------------------------------

def grade_rubric_items(rubric: dict, submission: str, options: dict, agent):
    results = []
    total_score = 0
    max_total = 0

    # SAFE LIMITS
    max_iterations = options.get("max_iterations", 2)
    timeout = options.get("timeout", 30)

    for item in rubric["rubric_items"]:
        start = time.time()
        prompt = item["prompt_template"].replace("{{submission}}", submission)

        try:
            # SAFE: enforce timeout + iteration limit
            response = asyncio.run(
                safe_agent_call(
                    agent=agent,
                    prompt=prompt,
                    max_iterations=max_iterations,
                    timeout=timeout
                )
            )

            score = extract_score(response.return_values)
            feedback = response.log

        except asyncio.TimeoutError:
            score = 0
            feedback = "ERROR: Timeout while grading item."

        except Exception as e:
            score = 0
            feedback = f"ERROR: {str(e)}"

        duration = time.time() - start

        results.append({
            "id": item["id"],
            "score": score,
            "max_score": item["max_score"],
            "feedback": feedback,
            "duration": duration,
        })

        total_score += score
        max_total += item["max_score"]

    return {
        "items": results,
        "total_score": total_score,
        "max_score": max_total,
        "percentage": (total_score / max_total) * 100 if max_total else 0
    }

async def safe_agent_call(agent, prompt, max_iterations, timeout):
    """Run agent.run() with a timeout wrapper."""
    loop = asyncio.get_event_loop()

    async def run_agent():
        return await loop.run_in_executor(
            None,
            lambda: agent.run(task=prompt, context={}, max_iterations=max_iterations)
        )

    # This enforces the timeout
    return await asyncio.wait_for(run_agent(), timeout=timeout)

def extract_score(output):
    try:
        return int(output.get("score", 0))
    except:
        return 0
