````markdown name=README.md url=https://github.com/brakower/Team-H/blob/98e944900f76d722926fa692aafeca5c6eca82b3/README.md
```markdown
# Team-H

A modern full-stack application that demonstrates a Python FastAPI backend (including a ReAct-style "React Agent" and dynamic tool system) and an Angular frontend for interactive demos.

This README summarizes project structure, setup, usage, API examples, testing instructions, and the project goals and user stories for COMP423-style automated grading.

---

## Table of contents

- Project structure
- About the project
- User stories
- Features
- Prerequisites
- Quick start (devcontainer / manual)
- Running the backend
- Running the frontend
- API examples
- Testing
- Contributing
- License & acknowledgements

---

## Project structure

Team-H/
├── .devcontainer/          # VS Code devcontainer configuration  
├── backend/                # Python backend (FastAPI + React Agent)  
│   ├── tests/              # unit tests  
│   ├── models/             # pydantic models
│   ├── services/           # backend services
│   ├── agent/              # ReAct Agent
│   ├── main.py             # FastAPI application entrypoint  
│   └── pyproject.toml      # Poetry configuration  
└── frontend/               # Angular frontend (demo UI & services)

---

## About the project

Modern AI Agents are capable of carrying out step-by-step tasks that call out to "tools" — functions written by software engineers — to carry out time-intensive or specialized tasks. Throughout this project, we develop an agent system (integrating with the OpenAI API) that can investigate a student's project code in a project-based learning course like COMP423.

What does it mean to "investigate"?
- The agent examines repository data (commits, tests, code structure, configuration) to look for evidence of rubric items and qualities expected from assignments. Examples: verifying test coverage, checking coding standards for FastAPI route definitions, inspecting commit history for appropriate incremental work, and verifying presence/quality of documentation.

Primary goals:
- Automate routine checks TAs currently perform so TAs can focus on higher-level feedback and guidance.
- Produce transparent logs/explanations for each rubric item so instructors and students can see why the agent graded a particular way.
- Make the tool adaptable and reusable across many CS courses with the goal of long-term adoption (e.g., becoming an official CSXL-supported tool).

---

## Features

Backend
- ReAct-style "React Agent" loop (Thought → Action → Observation)
- Tool registry with automatic JSON Schema generation for tool parameters
- FastAPI REST API exposing endpoints to list/discover tools and run the agent
- Pydantic models and comprehensive unit tests
- Integration points to add rubric parsers and batch grading workflows

Frontend
- Angular demo UI showing agent interactions
- TypeScript service with typed endpoints for backend communication
- Responsive components and reactive data flow (RxJS)
- Components to upload rubrics/github repositories and trigger batch grading (demo)

---

## Prerequisites

- Python 3.11+
- Node.js 20.x+ and npm
- Poetry (for Python dependency management)
- (Optional) VS Code with Dev Containers extension for reproducible development environment
- OpenAI API key (for agent LLM integration) — set via environment variable or secrets manager during deployment. Please reach out to developers or client for API keys.
- Sample demo files
   - Student submission with nested files: https://github.com/katie-cooper/agent-student-submission-files
   - Student submission with basic file structure: https://github.com/Jordweinstein/agent-student-submission
   - Sample rubric: /examples/student_example/rubric.json

---

## Quick start (recommended): VS Code devcontainer

1. Install the "Dev Containers" extension in VS Code.
2. Open the repository in VS Code.
3. Command Palette → "Dev Containers: Reopen in Container".
4. The container will build and run the post-create commands to install Python, Node, and dependencies.

This option gives a reproducible environment (Python 3.11, Node.js, npm, Poetry). If any errors arise related to poetry not finding a backend package, please note this is a further issue to be addressed in development. You may continue with the demo and development without issues despite this warning.

---

## Manual setup

Backend
1. cd backend
2. Install Poetry if needed:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   # or
   pip install poetry
   ```
3. Install dependencies:
   ```bash
   poetry install
   ```
4. Activate the virtual environment:
   ```bash
   poetry shell
   ```
5. Configure environment variables (example):
   ```bash
   export OPENAI_API_KEY="sk-..."
   export FASTAPI_ENV=development
   ```

Frontend
1. cd frontend
2. Install npm packages:
   ```bash
   npm install
   ```

---

## Run the services

Backend (development)
```bash
cd backend
# with poetry
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
# or
poetry run python main.py
```
API available at: http://localhost:8000  
Interactive docs (OpenAPI/Swagger): http://localhost:8000/docs

Frontend (development)
```bash
cd frontend
npm start
# or
npx ng serve --host 0.0.0.0 --port 4200
```
Open: http://localhost:4200

Run both simultaneously (two terminals): backend on 8000, frontend on 4200.

---

## API — Common endpoints

- GET /tools — list available tools
- GET /tools/{tool_name} — get schema/metadata for a tool
- POST /execute — execute a specific tool (body: tool_name + parameters)
- POST /run — run the agent for a given task (body: task, optional max_iterations)
- POST /grade/batch — (example) run batch grading for many submissions using a rubric
- GET /discover — returns discovered tools and their schemas
- GET /health — simple health check

Example: list tools
```bash
curl http://localhost:8000/tools
```

Example: execute a tool (calculator)
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "calculator",
    "parameters": {"operation": "add", "a": 5, "b": 3}
  }'
```

Example: run the agent
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "perform calculation", "max_iterations": 5}'
```

---

## Testing

Backend
```bash
cd backend
poetry run pytest         # run all tests
poetry run pytest -v      # verbose
poetry run pytest --cov=backend tests/
```
Key test files:
- tests/test_agent.py
- tests/test_tools.py
- tests/test_api.py

Frontend
```bash
cd frontend
npm test
# or
ng test
```

---

## Development notes & tips

- The backend auto-discovers tools and exposes their JSON schemas via the API; use those schemas to form correct requests from the frontend.
- When adding new tools, include JSON Schema annotations so the frontend and docs can render parameter forms automatically.
- If using CORS, confirm the backend allows requests from the frontend origin (http://localhost:4200) during development.
- For grading-specific features:
  - Rubrics should be uploaded in a structured format (JSON/YAML) so rules can be parsed into tool-driven checks.
  - Batch grading can be implemented as a job queue if scaling to many submissions.

---

## Contributing

Contributions welcome. Suggested workflow:
1. Fork the repository and create a feature branch (e.g., `feature/readme-improvements`).
2. Open a PR describing the change and include any relevant screenshots or logs.
3. Keep commits focused and include tests if behavior changes.

If you'd like, I can create a branch with this README update and open a PR — tell me whether to proceed and the branch/commit message to use.

---

## Acknowledgements

This repository demonstrates a small full-stack integration of modern Python backend tooling and a modern Angular frontend for demos and experimentation. The grading agent concept follows ReAct-style agent patterns and leverages LLMs for reasoning and structured tool calls.
