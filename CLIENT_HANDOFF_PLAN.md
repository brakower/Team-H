# Team H COMP 523 Client Hand-Off Plan

## Client Hand-Off Document

This document summarizes the final deliverables, system architecture, setup process, ownership details, operating costs, and recommended next steps for the Team H AI Agentic Grader project. It also includes the most recent update: a command-line grading workflow that can inspect student repository git history and verify required commits.

---

## Final Client Deliverables

1. Access to the public Team H repository with full AI agent grading functionality.
2. Detailed README documentation with setup instructions, backend details, and usage guidance.
3. Three client hand-off videos showing:
   - How to set up the development environment.
   - How to run the frontend and backend.
   - How to use the application.
4. Access to the team website, which includes materials for future developers such as the final architecture diagram, test plan, user manual, and additional project documentation.
5. Command-line grading support for running grading workflows against local student repositories, including git commit history checks.

---

## Project Overview

Team H built an AI-assisted grading application that combines a web interface, a FastAPI backend, and a ReAct-style AI agent. The system helps evaluate student code submissions using rubric-driven grading tools.

### Main Components

- **Angular Frontend:** Interactive UI for uploading rubrics, selecting rubric items, uploading or pointing to student repositories, running grading tasks, and viewing agent output.
- **Python Backend:** FastAPI server that exposes endpoints for grading, tool execution, uploads, GitHub repository cloning, and local batch grading.
- **AI Agent System:** ReAct-style agent that reasons through grading tasks and calls backend tools such as syntax checks, required element checks, style checks, documentation checks, pytest execution, and final grade computation.
- **Command-Line Grader:** A new script-based workflow for running grading from the terminal without using the browser. This is especially useful for batch grading and git-history-based rubric checks.
- **Git History Tooling:** New backend tooling that inspects a cloned repository's actual git commit history and checks for required commit messages or minimum commit counts.

The system allows users to interact with the AI agent through a web interface, run grading tasks, and view results in real time. The new CLI workflow also allows grading to be run directly from the terminal for local repositories or folders of submissions.

---

## 1. System Description

### Type of System

Locally hosted web application with an AI-powered Python backend and an optional command-line grading workflow.

### Access

There is currently no login or authentication layer implemented. OpenAI-compatible API credentials are required to run the AI agent. These keys were provided by the client, so the client will continue to manage access to the model provider.

### Ownership

The client will assume full ownership of the system upon handoff. All code, documentation, and deployment knowledge will be transferred through the repository, README, team website, and hand-off videos.

### Technical Stack Overview

- **Frontend:** Angular, TypeScript, Node.js, npm
- **Backend:** Python 3.11+, FastAPI, Poetry
- **AI Components:** ReAct-style agent using OpenAI-compatible GPT model access
- **Repository Processing:** Local file-system access, GitHub repository cloning, git command-line inspection
- **Command-Line Support:** Python CLI script located at `scripts/grade_submissions_cli.py`
- **Database:** No production database is required for the current local version of the application. Current grading state and results are handled through the application runtime, local files, and API responses.

---

## 2. Deployment and Setup

These instructions are also detailed in the README and demonstrated in the client hand-off videos.

### Prerequisites

- Python 3.11+
- Node.js 20.x+ and npm
- Poetry for Python dependency management
- Git
- Optional: VS Code with the Dev Containers extension for a reproducible development environment
- OpenAI-compatible API credentials for agent LLM integration

### Necessary Environment Variables

The backend expects the following values from the example `.env` configuration:

```text
UNC_OPENAI_API_KEY
UNC_OPENAI_API_ENDPOINT
UNC_OPENAI_API_VERSION
UNC_OPENAI_MODEL
```

Please reach out to the client or project developers for the credentials needed to run the application.

### Sample Demo Files

- Student submission with nested files: <https://github.com/katie-cooper/agent-student-submission-files>
- Student submission with basic file structure: <https://github.com/Jordweinstein/agent-student-submission>
- Sample rubric: `examples/student_example/rubric.json`

---

## 3. Recommended Environment Setup: Dev Container

1. Clone the repository:

```bash
git clone https://github.com/brakower/Team-H.git
cd Team-H
```

2. Open the project in VS Code.
3. Install the **Dev Containers** extension.
4. Press `F1` and select:

```text
Dev Containers: Reopen in Container
```

5. The container installs the expected Python, Node.js, npm, and Poetry environment.

Note: This option provides a reproducible environment using Python 3.11, Node.js, npm, and Poetry. If Poetry reports a backend package warning, the application can still be developed and demonstrated, but that warning should be reviewed in future maintenance.

---

## 4. Running the Web Application

### Start the Backend

Open a terminal and run:

```bash
cd backend
poetry run python main.py
```

Alternatively:

```bash
cd backend
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start the Frontend

Open a second terminal and run:

```bash
cd frontend
npx ng serve --host 0.0.0.0 --port 4200
```

Alternatively:

```bash
cd frontend
npm start
```

### Local URLs

- Frontend: <http://localhost:4200/>
- Backend: <http://localhost:8000/>

---

## 5. New CLI Git-History Grading Workflow

A new command-line workflow has been added so grading can be run without using the browser. This supports the client’s requested next step of pointing the grader at student repositories and inspecting actual git commit history.

### New Files Added

```text
scripts/grade_submissions_cli.py
backend/tools/git_tools.py
```

### Git-History Tooling

The new git tooling reads commit history from a cloned repository. Because a normal `git clone` includes `.git` history, the tool can run git commands against the local clone.

The main git-history checks include:

- Reading recent commits.
- Returning commit hash, short hash, author, email, date, and message.
- Checking for one or more required commit messages.
- Checking for a minimum number of commits.
- Returning structured pass/fail output.

### Example: Test Git History on the Current Repo

From the backend directory:

```bash
cd /workspaces/Team-H/backend

poetry run python ../scripts/grade_submissions_cli.py \
  --submissions .. \
  --rubric ../examples/student_example/rubric.json \
  --selected git_history \
  --required-commit "initial commit" \
  --min-commits 1
```

Expected behavior:

- The CLI finds the repository.
- The git-history tool reads the actual commit history.
- The output includes `passed`, `score`, `found_messages`, `missing_messages`, `total_commits`, and commit metadata.

### Example: Grade a Folder of Student Repositories

If each student submission is a cloned repository inside a submissions folder:

```bash
cd backend

poetry run python ../scripts/grade_submissions_cli.py \
  --submissions ../examples/submissions \
  --rubric ../examples/student_example/rubric.json \
  --selected git_history \
  --required-commit "initial commit" \
  --min-commits 3 \
  --output results.json
```

The CLI treats each child directory as an individual student repository, runs the selected checks, and writes structured JSON results when `--output` is provided.

### When to Use the CLI Instead of the Browser

Use the CLI when:

- Grading many local student repositories.
- Checking objective rubric requirements such as commit history.
- Running grading in a reproducible terminal workflow.
- Avoiding frontend setup for quick checks.
- Integrating grading into future automation or scripts.

Use the browser when:

- Demonstrating the interactive application.
- Uploading rubrics or repositories through the UI.
- Viewing step-by-step agent output in a user-friendly format.

---

## 6. Client Ownership and Costs

### Ownership Transfer

Upon completion, all code, documentation, and setup instructions will be transferred to the client.

### Credentials

OpenAI-compatible API credentials were client-provided, so the client already controls access to the model provider. These keys should remain private and should not be committed to the repository.

### Code

The repository is public and has been shared with the client:

<https://github.com/brakower/Team-H.git>

### Documentation

The team website is available here:

<https://tarheels.live/comp523teamh/>

The README also includes project setup and usage details.

### Hosting and Usage Costs

The application is currently designed for local hosting. Costs depend primarily on model usage.

Potential costs include:

- OpenAI-compatible API usage.
- Any future hosting provider selected by the client.
- Any future database, storage, or authentication service if the system is extended.

Model calls consume tokens, so costs scale with usage. Heavier use, longer prompts, larger responses, or more concurrent users will increase costs.

---

## 7. Recommendations

### Training

We recommend watching the hand-off videos before running or modifying the system.

- Setting up your environment: <https://www.youtube.com/watch?v=xLGGQjgNT14>
- Running your frontend and backend: <https://www.youtube.com/watch?v=2B2d52GgK74>
- Using the AI agent: <https://www.youtube.com/watch?v=h5KkHFPOI0E>

### Development Recommendations

Future developers should consider the following improvements:

1. Expand CLI grading beyond git history to support syntax checks, pytest checks, documentation checks, style checks, and final grade aggregation.
2. Keep deterministic checks, such as commit history and test execution, outside the LLM loop when possible.
3. Use the AI agent for reasoning-heavy rubric items and explanation generation.
4. Improve nested file traversal for repository analysis.
5. Remove or replace any hardcoded example paths in grading tools.
6. Add clearer error handling when repositories are missing `.git` history.
7. Add automated tests for the new CLI and git-history tool.
8. Consider adding authentication if the system is deployed beyond a local or controlled environment.

### Support Window

A two-week post-handoff support window is recommended for troubleshooting setup, environment, deployment, and usage issues.

---

## 8. Final Actions for Client Handoff

1. Confirm the client’s preferred method for receiving final code and deployment files.
2. Confirm the client has access to the public GitHub repository.
3. Confirm the client has access to required API credentials.
4. Review the README and team website documentation with the client.
5. Walk through the three hand-off videos.
6. Demonstrate both workflows:
   - Browser-based grading through the Angular frontend.
   - Command-line git-history grading through `scripts/grade_submissions_cli.py`.
7. Review and approve this hand-off plan.

---

## 9. Further Support

If questions or deployment issues arise, please contact the team through the project website:

<https://tarheels.live/comp523teamh/>

### Team Roles

- Jordan Weinstein: Client Manager
- Katie Fort: Project Manager
- Bennett Rakower: Technical Lead
- Yashu Tanneru: Scrum Master
