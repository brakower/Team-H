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
