#!/usr/bin/env python3

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

from agent import ReactAgent, ToolRegistry
from tools.grading_tools import (
    load_rubric,
    list_repo_files,
    load_submission,
    load_test_cases,
    check_syntax,
    check_required_elements,
    check_documentation_tools,
    check_style_tools,
    run_functional_tests,
    compute_final_grade,
)
from tools.testing_tools import run_pytest_on_directory
from tools.git_tools import get_git_history, check_git_history


def build_registry():
    registry = ToolRegistry()

    registry.register_tool(
        "get_git_history",
        get_git_history,
        "Read commit history from a cloned git repository",
        {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "max_commits": {"type": "integer"},
            },
            "required": ["repo_path"],
        },
    )

    registry.register_tool(
        "check_git_history",
        check_git_history,
        "Check git commit history for required messages or minimum commit count",
        {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "required_messages": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "required_message": {"type": "string"},
                "min_commits": {"type": "integer"},
                "match_mode": {"type": "string"},
                "case_sensitive": {"type": "boolean"},
                "max_commits": {"type": "integer"},
            },
            "required": ["repo_path"],
        },
    )

    registry.register_tool(
        "run_pytest_on_directory",
        run_pytest_on_directory,
        "Run pytest on a directory",
        {
            "type": "object",
            "properties": {"directory_path": {"type": "string"}},
            "required": ["directory_path"],
        },
    )

    registry.register_tool(
        "load_rubric",
        load_rubric,
        "Load rubric",
        {
            "type": "object",
            "properties": {
                "rubric_path": {"type": "string"},
                "rubric": {"type": "object"},
                "selected_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    )

    registry.register_tool(
        "list_repo_files",
        list_repo_files,
        "List repo files",
        {
            "type": "object",
            "properties": {"repo_path": {"type": "string"}},
            "required": ["repo_path"],
        },
    )

    registry.register_tool(
        "load_submission",
        load_submission,
        "Load submission",
        {
            "type": "object",
            "properties": {"submission_path": {"type": "string"}},
            "required": ["submission_path"],
        },
    )

    registry.register_tool(
        "load_test_cases",
        load_test_cases,
        "Load test cases",
        {
            "type": "object",
            "properties": {"test_cases_path": {"type": "string"}},
            "required": ["test_cases_path"],
        },
    )

    registry.register_tool(
        "check_syntax",
        check_syntax,
        "Check syntax",
        {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "repo_path": {"type": "string"},
            },
        },
    )

    registry.register_tool(
        "check_required_elements",
        check_required_elements,
        "Check required code elements",
        {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "repo_path": {"type": "string"},
                "required_items": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    )

    registry.register_tool(
        "check_documentation_tools",
        check_documentation_tools,
        "Check documentation",
        {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "repo_path": {"type": "string"},
            },
        },
    )

    registry.register_tool(
        "check_style_tools",
        check_style_tools,
        "Check style",
        {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "repo_path": {"type": "string"},
            },
        },
    )

    registry.register_tool(
        "run_functional_tests",
        run_functional_tests,
        "Run functional tests",
        {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "test_cases": {"type": "array"},
            },
        },
    )

    registry.register_tool(
        "compute_final_grade",
        compute_final_grade,
        "Compute final grade",
        {
            "type": "object",
            "properties": {
                "rubric": {"type": "object"},
                "syntax": {"type": "object"},
                "required": {"type": "object"},
                "documentation": {"type": "object"},
                "style": {"type": "object"},
                "tests": {"type": "object"},
                "git_history": {"type": "object"},
            },
        },
    )

    return registry


def find_repos(submissions_dir):
    submissions_dir = Path(submissions_dir).resolve()

    if (submissions_dir / ".git").exists():
        return [submissions_dir]

    return [
        child
        for child in sorted(submissions_dir.iterdir())
        if child.is_dir() and not child.name.startswith(".")
    ]


async def run_agent_on_repo(repo_path, rubric_path, selected, required_commits, min_commits):
    if "git_history" in selected:
        git_result = check_git_history(
            repo_path=str(repo_path),
            required_messages=required_commits,
            min_commits=min_commits,
        )

        return {
            "repo": repo_path.name,
            "repo_path": str(repo_path),
            "result": {
                "git_history": git_result,
            },
            "log": "Checked git history directly from CLI.",
        }

    registry = build_registry()
    agent = ReactAgent(registry, max_iterations=10)

    context = {
        "repo_path": str(repo_path),
        "rubric_path": str(rubric_path),
        "selected_ids": selected,
        "rubric_items": selected,
        "git_history_required_messages": required_commits,
        "min_commits": min_commits,
    }

    prompt = f"""
Grade this student repository.

Repository path:
{repo_path}

Use the selected rubric items:
{selected}

If git history is selected, inspect the actual git commit history.
"""

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: agent.run(prompt, context))

    return {
        "repo": repo_path.name,
        "repo_path": str(repo_path),
        "result": result.return_values,
        "log": result.log,
    }


async def main_async(args):
    repos = find_repos(args.submissions)
    results = []

    for repo in repos:
        print(f"Grading {repo.name}...", file=sys.stderr)
        result = await run_agent_on_repo(
            repo_path=repo,
            rubric_path=Path(args.rubric).resolve(),
            selected=args.selected,
            required_commits=args.required_commit or [],
            min_commits=args.min_commits,
        )
        results.append(result)

    payload = {
        "count": len(results),
        "results": results,
    }

    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2))
        print(f"Wrote results to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submissions", required=True)
    parser.add_argument("--rubric", required=True)
    parser.add_argument("--selected", nargs="+", default=["git_history"])
    parser.add_argument("--required-commit", action="append")
    parser.add_argument("--min-commits", type=int)
    parser.add_argument("--output")

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()