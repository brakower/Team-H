import json
import ast
import tempfile
import os
from typing import Dict, Any, Optional, List

from backend.tools.analysis_tools import (
    _is_valid_syntax,
    _extract_elements,
    _check_style,
    _check_documentation,
    _run_test_cases,
)

def grade_python_assignment(
    rubric_path: str,
    submission_path: str,
    test_cases_path: Optional[str] = None
) -> Dict[str, Any]:
    """Grade a Python coding assignment based on a rubric from files.

    Args:
        rubric_path: Path to JSON file containing grading rubric
        submission_path: Path to the student's Python file
        test_cases_path: Optional path to JSON file with test cases

    Returns:
        Dictionary containing grade breakdown, total score, and feedback
    """
    # Read rubric from file
    # TEMP: HARD-CODED PATH, replace with below comments for dynamic acceptance of parameters
    # with open(rubric_path, 'r') as f:
    #     rubric = json.load(f)
    with open('/workspaces/Team-H/examples/student_example/rubric.json', 'r') as f:
        rubric = json.load(f)
    
    # Read student code from file
    # TEMP: HARD-CODED PATH, replace with below comments for dynamic acceptance of parameters
    with open('/workspaces/Team-H/examples/student_example/student_submission.py', 'r') as f:
        student_code = f.read()
    
    # Read test cases if provided
    # TEMP: HARD-CODED PATH, replace with below comments for dynamic acceptance of parameters
    # test_cases = None
    # if test_cases_path and os.path.exists(test_cases_path):
    #     with open(test_cases_path, 'r') as f:
    #         test_cases = json.load(f)
    test_cases = None
    if test_cases_path:
        with open('/workspaces/Team-H/examples/student_example/test_cases.json', 'r') as f:
            test_cases = json.load(f)
    
    # Initialize results
    results = {
        "student_file": os.path.basename(submission_path),
        "total_score": 0,
        "max_score": 0,
        "breakdown": {},
        "feedback": []
    }
    
    # Parse rubric and initialize scores
    for category, criteria in rubric.items():
        results["breakdown"][category] = {
            "earned": 0,
            "possible": criteria.get("points", 0),
            "feedback": []
        }
        results["max_score"] += criteria.get("points", 0)
    
    # 1. Check syntax validity
    if "syntax" in rubric:
        try:
            ast.parse(student_code)
            results["breakdown"]["syntax"]["earned"] = rubric["syntax"]["points"]
            results["breakdown"]["syntax"]["feedback"].append("✓ Code has valid syntax")
        except SyntaxError as e:
            results["breakdown"]["syntax"]["feedback"].append(f"✗ Syntax error: {e}")
    
    # 2. Check for required elements (functions, classes, imports)
    if "required_elements" in rubric:
        tree = ast.parse(student_code) if _is_valid_syntax(student_code) else None
        if tree:
            required = rubric["required_elements"].get("items", [])
            found_elements = _extract_elements(tree)
            
            points_per_item = rubric["required_elements"]["points"] / len(required) if required else 0
            for item in required:
                if item in found_elements:
                    results["breakdown"]["required_elements"]["earned"] += points_per_item
                    results["breakdown"]["required_elements"]["feedback"].append(f"✓ Found: {item}")
                else:
                    results["breakdown"]["required_elements"]["feedback"].append(f"✗ Missing: {item}")
    
    # 3. Check documentation/comments
    if "documentation" in rubric:
        tree = ast.parse(student_code) if _is_valid_syntax(student_code) else None
        if tree:
            doc_score = _check_documentation(tree, student_code)
            max_doc = rubric["documentation"]["points"]
            results["breakdown"]["documentation"]["earned"] = doc_score * max_doc
            if doc_score >= 0.8:
                results["breakdown"]["documentation"]["feedback"].append("✓ Well documented")
            elif doc_score >= 0.5:
                results["breakdown"]["documentation"]["feedback"].append("⚠ Partial documentation")
            else:
                results["breakdown"]["documentation"]["feedback"].append("✗ Poor documentation")
    
    # 4. Run test cases
    if "functionality" in rubric and test_cases:
        passed, total, feedback = _run_test_cases(student_code, test_cases)
        if total > 0:
            results["breakdown"]["functionality"]["earned"] = (passed / total) * rubric["functionality"]["points"]
            results["breakdown"]["functionality"]["feedback"].append(f"Passed {passed}/{total} test cases")
            results["breakdown"]["functionality"]["feedback"].extend(feedback)
    
    # 5. Check code style/quality
    if "style" in rubric:
        style_score = _check_style(student_code)
        results["breakdown"]["style"]["earned"] = style_score * rubric["style"]["points"]
        if style_score >= 0.8:
            results["breakdown"]["style"]["feedback"].append("✓ Good code style")
        else:
            results["breakdown"]["style"]["feedback"].append("⚠ Could improve code style")
    
    # Calculate total score
    for category in results["breakdown"].values():
        results["total_score"] += category["earned"]
    
    # Round scores
    results["total_score"] = round(results["total_score"], 2)
    for category in results["breakdown"].values():
        category["earned"] = round(category["earned"], 2)
    
    # Generate overall feedback
    percentage = (results["total_score"] / results["max_score"] * 100) if results["max_score"] > 0 else 0
    results["percentage"] = round(percentage, 1)
    
    return results