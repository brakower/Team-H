import os
import subprocess


def _run_git(repo_path, args, timeout=10):
    return subprocess.run(
        ["git", "-C", os.path.abspath(repo_path), *args],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def get_git_history(repo_path, max_commits=25):
    proc = _run_git(
        repo_path,
        [
            "log",
            f"--max-count={max_commits}",
            "--date=iso-strict",
            "--pretty=format:%H%x1f%h%x1f%an%x1f%ae%x1f%ad%x1f%s",
        ],
    )

    if proc.returncode != 0:
        return {
            "passed": False,
            "error": proc.stderr.strip(),
            "repo_path": repo_path,
        }

    commits = []
    for line in proc.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 6:
            commits.append(
                {
                    "hash": parts[0],
                    "short_hash": parts[1],
                    "author_name": parts[2],
                    "author_email": parts[3],
                    "date": parts[4],
                    "message": parts[5],
                }
            )

    count_proc = _run_git(repo_path, ["rev-list", "--count", "HEAD"])

    return {
        "passed": True,
        "repo_path": repo_path,
        "total_commits": int(count_proc.stdout.strip()) if count_proc.returncode == 0 else len(commits),
        "commits": commits,
    }


def check_git_history(
    repo_path,
    required_messages=None,
    required_message=None,
    min_commits=None,
    match_mode="contains",
    case_sensitive=False,
    max_commits=100,
):
    history = get_git_history(repo_path, max_commits=max_commits)

    if not history.get("passed"):
        return {
            "passed": False,
            "score": 0,
            "history": history,
            "explanation": "Could not read git history.",
        }

    requirements = []
    if required_messages:
        requirements.extend(required_messages)
    if required_message:
        requirements.append(required_message)

    messages = [commit["message"] for commit in history["commits"]]

    if not case_sensitive:
        compare_messages = [m.lower() for m in messages]
        compare_requirements = [r.lower() for r in requirements]
    else:
        compare_messages = messages
        compare_requirements = requirements

    found = []
    missing = []

    for original, requirement in zip(requirements, compare_requirements):
        if match_mode == "exact":
            matched = any(msg == requirement for msg in compare_messages)
        else:
            matched = any(requirement in msg for msg in compare_messages)

        if matched:
            found.append(original)
        else:
            missing.append(original)

    commit_count_ok = True
    if min_commits is not None:
        commit_count_ok = history["total_commits"] >= min_commits

    passed = len(missing) == 0 and commit_count_ok

    return {
        "passed": passed,
        "score": 1 if passed else 0,
        "found_messages": found,
        "missing_messages": missing,
        "min_commits": min_commits,
        "commit_count_ok": commit_count_ok,
        "history": history,
        "explanation": f"Found {len(found)}/{len(requirements)} required commit messages.",
    }