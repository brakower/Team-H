"""Example tools for the React Agent."""

from typing import List, Dict, Any
import json


def calculator(operation: str, a: float, b: float) -> float:
    """Perform basic arithmetic operations.

    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number

    Returns:
        Result of the operation
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float("inf"),
    }

    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")

    return operations[operation](a, b)


def string_analyzer(text: str) -> Dict[str, Any]:
    """Analyze a string and return statistics.

    Args:
        text: The text to analyze

    Returns:
        Dictionary with text statistics
    """
    words = text.split()
    return {
        "length": len(text),
        "word_count": len(words),
        "unique_words": len(set(words)),
        "average_word_length": (
            sum(len(word) for word in words) / len(words) if words else 0
        ),
    }


def list_processor(items: List[str], operation: str) -> Any:
    """Process a list of items.

    Args:
        items: List of items to process
        operation: Operation to perform (count, sort, reverse, unique)

    Returns:
        Processed result
    """
    operations = {
        "count": lambda x: len(x),
        "sort": lambda x: sorted(x),
        "reverse": lambda x: list(reversed(x)),
        "unique": lambda x: list(set(x)),
    }

    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")

    return operations[operation](items)


def json_formatter(data: Dict[str, Any], indent: int = 2) -> str:
    """Format a dictionary as JSON.

    Args:
        data: Dictionary to format
        indent: Number of spaces for indentation

    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent)

import ast
import json
from typing import Dict, List, Any, Optional
import tempfile
import os

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


def _is_valid_syntax(code: str) -> bool:
    """Check if code has valid syntax."""
    try:
        ast.parse(code)
        return True
    except:
        return False


def _extract_elements(tree: ast.AST) -> List[str]:
    """Extract function and class names from AST."""
    elements = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            elements.append(node.name)
        elif isinstance(node, ast.ClassDef):
            elements.append(node.name)
    return elements


def _check_documentation(tree: ast.AST, code: str) -> float:
    """Check documentation quality (0.0 to 1.0)."""
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not functions:
        return 1.0
    
    documented = sum(1 for f in functions if ast.get_docstring(f))
    has_comments = "#" in code
    
    doc_ratio = documented / len(functions) if functions else 0
    return min(1.0, doc_ratio + (0.2 if has_comments else 0))


def _check_style(code: str) -> float:
    """Basic style check (0.0 to 1.0)."""
    score = 1.0
    lines = code.split('\n')
    
    # Check for extremely long lines
    if any(len(line) > 120 for line in lines):
        score -= 0.2
    
    # Check for reasonable spacing
    if '\n\n\n\n' in code:
        score -= 0.1
    
    # Check for basic naming (no single letters except loop vars)
    if any(word in code.split() for word in ['aa', 'bb', 'xxx', 'tmp123']):
        score -= 0.2
    
    return max(0.0, score)


def _run_test_cases(code: str, test_cases: List[Dict[str, Any]]) -> tuple:
    """Run test cases against the code."""
    passed = 0
    feedback = []
    
    # Create temporary file with student code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("student_module", temp_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        for i, test in enumerate(test_cases):
            try:
                func_name = test.get("function")
                inputs = test.get("inputs", [])
                expected = test.get("expected")
                
                if not hasattr(module, func_name):
                    feedback.append(f"✗ Test {i+1}: Function '{func_name}' not found")
                    continue
                
                func = getattr(module, func_name)
                result = func(*inputs) if isinstance(inputs, list) else func(**inputs)
                
                if result == expected or (isinstance(expected, float) and abs(result - expected) < 1e-9):
                    passed += 1
                    feedback.append(f"✓ Test {i+1}: Passed")
                else:
                    feedback.append(f"✗ Test {i+1}: Expected {expected}, got {result}")
            except Exception as e:
                feedback.append(f"✗ Test {i+1}: Error - {str(e)[:50]}")
    except Exception as e:
        feedback.append(f"✗ Could not execute code: {str(e)[:100]}")
    finally:
        os.unlink(temp_file)
    
    return passed, len(test_cases), feedback

import subprocess
import json
import tempfile
import os
from typing import Dict, Any


def run_pytest_on_directory(directory_path: str) -> Dict[str, Any]:
    """
    Run pytest inside a student submission folder and return structured results.

    Args:
        directory_path: Path to the folder containing the student's tests
                        (e.g., /workspaces/Team-H/examples/student_example)

    Returns:
        Dictionary with:
        - total_tests
        - passed
        - failed
        - errors
        - skipped
        - report (full text output from pytest)
    """
    # Ensure directory exists
    directory_path = '/workspaces/Team-H/examples/student_example'
    if not os.path.isdir(directory_path):
        return {"error": f"Directory not found: {directory_path}"}

    # Run pytest with JSON reporting enabled
    try:
        # Create a temporary output file for the JSON test report
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            json_report_path = tmp.name

        cmd = [
            "pytest",
            "-q",
            directory_path,
            f"--json-report",
            f"--json-report-file={json_report_path}"
        ]

        # Execute pytest and capture console output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        # Attempt to load pytest's generated structured report
        if os.path.exists(json_report_path):
            with open(json_report_path, "r") as f:
                report = json.load(f)
        else:
            report = None

        # Parse summary
        summary = report.get("summary", {}) if report else {}
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        errors = summary.get("errors", 0)
        skipped = summary.get("skipped", 0)

        total_tests = passed + failed + errors + skipped

        return {
            "directory": directory_path,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "console_output": stdout,
            "error_output": stderr
        }

    except Exception as e:
        return {"error": f"Failed to run pytest: {str(e)}"}
    finally:
        # Clean up
        if os.path.exists(json_report_path):
            os.unlink(json_report_path)
