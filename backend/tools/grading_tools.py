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

def check_syntax(code: Optional[str] = None, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """Check whether the student's code has valid Python syntax.

    Accepts either a `code` string, a single `code` file path, or a `repo_path`
    directory. When `repo_path` is provided it takes precedence and all `.py`
    files under the directory are checked.
    """
    # prefer repo_path when supplied
    if repo_path:
        code = repo_path
    # If `code` is a directory path, walk and parse all .py files
    if isinstance(code, str) and os.path.isdir(code):
        repo_path = code
        errors = []
        files_checked = 0
        skip_dirs = {"__pycache__", ".git", "node_modules", "venv", ".venv"}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                # store paths relative to the repository root to avoid leaking
                # the full absolute path in results
                rel_path = os.path.relpath(fpath, repo_path) if repo_path else fpath
                files_checked += 1
                try:
                    txt = open(fpath, 'r', encoding='utf-8').read()
                except Exception as e:
                    errors.append({"file": rel_path, "error": f"read error: {e}"})
                    continue

                try:
                    ast.parse(txt)
                except SyntaxError as e:
                    errors.append({"file": rel_path, "error": str(e)})

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "files_checked": files_checked,
        }

    # If `code` is a filepath, read and parse that file
    if isinstance(code, str) and os.path.isfile(code):
        try:
            txt = open(code, 'r', encoding='utf-8').read()
        except Exception as e:
            return {"valid": False, "errors": [{"file": code, "error": f"read error: {e}"}], "files_checked": 0}

        try:
            ast.parse(txt)
            return {"valid": True, "errors": [], "files_checked": 1}
        except SyntaxError as e:
            return {"valid": False, "errors": [{"file": code, "error": str(e)}], "files_checked": 1}

    # Otherwise assume `code` is a source string
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


def check_required_elements(code: Optional[str] = None, required_items: Optional[List[str]] = None, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Check whether required functions or classes appear in the provided input.

    The `code` parameter is flexible:
    - If `code` is a path to a directory, the function will walk the directory,
      parse only `.py` files, and aggregate found elements across files.
    - If `code` is a path to a file, that file will be read and analyzed.
    - Otherwise, `code` is treated as a Python source string and parsed directly.

    This keeps backwards compatibility while adding a minimal repo-wide
    `.py`-only scan when given a repository path.
    """

    # Helper: aggregate results from a single AST-parsed tree
    def _found_from_tree(tree) -> List[str]:
        try:
            return _extract_elements(tree)
        except Exception:
            return []

    # prefer repo_path when supplied
    if repo_path:
        code = repo_path

    # 1) If `code` is a directory, walk and inspect .py files only and record where items are found
    if isinstance(code, str) and os.path.isdir(code):
        repo_path = code
        found_map: Dict[str, List[str]] = {r: [] for r in required_items}
        found_set = set()
        # skip common noisy dirs
        skip_dirs = {"__pycache__", ".git", "node_modules", "venv", ".venv"}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, repo_path) if repo_path else fpath
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        txt = f.read()
                except Exception:
                    continue

                if not _is_valid_syntax(txt):
                    continue

                try:
                    tree = ast.parse(txt)
                except Exception:
                    continue

                for name in _found_from_tree(tree):
                    if name in found_map:
                        found_map[name].append(rel)
                    found_set.add(name)

        found = sorted(list(found_set))
        missing = [r for r in required_items if r not in found]
        # include a files mapping for where each required item was found
        files_info = {k: v for k, v in found_map.items() if v}
        return {"found": found, "missing": missing, "files": files_info}

    # 2) If `code` is a path to a file, read and analyze that file
    if isinstance(code, str) and os.path.isfile(code):
        try:
            with open(code, 'r', encoding='utf-8') as f:
                txt = f.read()
        except Exception:
            return {"found": [], "missing": required_items}

        if not _is_valid_syntax(txt):
            return {"found": [], "missing": required_items}

        try:
            tree = ast.parse(txt)
        except Exception:
            return {"found": [], "missing": required_items}

        found = _found_from_tree(tree)
        missing = [r for r in required_items if r not in found]
        # map found items to this single file
        files_info = {item: [code] for item in found}
        return {"found": found, "missing": missing, "files": files_info}

    # 3) Otherwise treat `code` as a source string
    if not _is_valid_syntax(code):
        return {"found": [], "missing": required_items}

    tree = ast.parse(code)
    found = _found_from_tree(tree)
    missing = [r for r in required_items if r not in found]

    # in-memory code string: we cannot report file paths
    return {"found": found, "missing": missing, "files": {}}


def check_documentation_tools(code: Optional[str] = None, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """Check docstrings and comments using your helper scoring.

    Accepts either a source string, a file path, or a repository directory.
    When given a directory, only `.py` files are inspected and results are
    aggregated. Returns an aggregate `score` plus per-file feedback mapping
    under the `files` key.
    """
    # prefer repo_path when supplied
    if repo_path:
        code = repo_path

    # If directory, iterate .py files
    if isinstance(code, str) and os.path.isdir(code):
        repo_path = code
        scores = []
        files_feedback: Dict[str, Any] = {}
        skip_dirs = {"__pycache__", ".git", "node_modules", "venv", ".venv"}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, repo_path) if repo_path else fpath
                try:
                    txt = open(fpath, 'r', encoding='utf-8').read()
                except Exception:
                    continue

                if not _is_valid_syntax(txt):
                    files_feedback[rel] = {"score": 0.0, "feedback": "Invalid syntax"}
                    continue

                try:
                    tree = ast.parse(txt)
                except Exception:
                    files_feedback[rel] = {"score": 0.0, "feedback": "Parse error"}
                    continue

                s = _check_documentation(tree, txt)
                label = ("Well documented" if s >= 0.8 else
                         "Partial documentation" if s >= 0.5 else
                         "Poor documentation")
                files_feedback[rel] = {"score": s, "feedback": label}
                scores.append(s)

        overall = (sum(scores) / len(scores)) if scores else 0.0
        return {"score": overall, "feedback": [f"{f}: {files_feedback[f]['feedback']}" for f in files_feedback], "files": files_feedback}

    # If file path, analyze single file
    if isinstance(code, str) and os.path.isfile(code):
        try:
            txt = open(code, 'r', encoding='utf-8').read()
        except Exception:
            return {"score": 0.0, "feedback": "Could not read file", "files": {}}

        if not _is_valid_syntax(txt):
            return {"score": 0.0, "feedback": "Invalid syntax", "files": {code: {"score": 0.0, "feedback": "Invalid syntax"}}}

        try:
            tree = ast.parse(txt)
        except Exception:
            return {"score": 0.0, "feedback": "Parse error", "files": {code: {"score": 0.0, "feedback": "Parse error"}}}

        s = _check_documentation(tree, txt)
        label = ("Well documented" if s >= 0.8 else
                 "Partial documentation" if s >= 0.5 else
                 "Poor documentation")
        return {"score": s, "feedback": label, "files": {code: {"score": s, "feedback": label}}}

    # Otherwise treat input as source string
    if code is None or not _is_valid_syntax(code):
        return {"score": 0.0, "feedback": "Invalid syntax, cannot analyze documentation"}

    tree = ast.parse(code)
    score = _check_documentation(tree, code)

    return {
        "score": score,
        "feedback": (
            "Well documented" if score >= 0.8 else
            "Partial documentation" if score >= 0.5 else
            "Poor documentation"
        ),
        "files": {}
    }


def check_style_tools(code: Optional[str] = None, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """Check basic style using your scoring system."""
    # prefer repo_path when supplied
    if repo_path:
        code = repo_path

    # If directory, compute per-file style and aggregate
    if isinstance(code, str) and os.path.isdir(code):
        repo_path = code
        scores = []
        files_feedback: Dict[str, Any] = {}
        skip_dirs = {"__pycache__", ".git", "node_modules", "venv", ".venv"}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, repo_path) if repo_path else fpath
                try:
                    txt = open(fpath, 'r', encoding='utf-8').read()
                except Exception:
                    continue

                s = _check_style(txt)
                label = ("Good style" if s >= 0.8 else "Could improve style")
                files_feedback[rel] = {"score": s, "feedback": label}
                scores.append(s)

        overall = (sum(scores) / len(scores)) if scores else 0.0
        return {"score": overall, "feedback": [f"{f}: {files_feedback[f]['feedback']}" for f in files_feedback], "files": files_feedback}

    # If file path
    if isinstance(code, str) and os.path.isfile(code):
        try:
            txt = open(code, 'r', encoding='utf-8').read()
        except Exception:
            return {"score": 0.0, "feedback": "Could not read file", "files": {}}

        s = _check_style(txt)
        label = ("Good style" if s >= 0.8 else "Could improve style")
        return {"score": s, "feedback": label, "files": {code: {"score": s, "feedback": label}}}

    # Otherwise assume source string
    if code is None:
        return {"score": 0.0, "feedback": "No code provided", "files": {}}

    score = _check_style(code)
    return {
        "score": score,
        "feedback": (
            "Good style" if score >= 0.8 else
            "Could improve style"
        ),
        "files": {}
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
            # Support new shape where syntax reports per-file `errors` list
            if syntax:
                if syntax.get("error"):
                    feedback = [f"✗ Syntax error: {syntax.get('error')}"]
                elif syntax.get("errors"):
                    errs = syntax.get("errors")
                    # show up to first 3 file errors
                    preview = [f"{e.get('file')}: {e.get('error')}" for e in errs[:3]]
                    feedback = ["✗ Syntax errors in files:"] + preview
                else:
                    feedback = ["✗ Syntax check failed or not run"]
            else:
                feedback = ["✗ Syntax check failed or not run"]

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
        files_map = required.get("files", {}) if required else {}
        for item in required_items:
            if required and item in required.get("found", []):
                locations = files_map.get(item)
                if locations:
                    feedback.append(f"✓ Found: {item} (in: {', '.join(locations)})")
                else:
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
