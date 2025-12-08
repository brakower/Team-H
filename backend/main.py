"""FastAPI application for the React Agent backend."""
import json
from fastapi import Body, FastAPI, HTTPException, File, UploadFile
import tempfile
import os
from git import Repo
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from models.rubric_schema import RubricItem, RubricSchema
import asyncio
import time

from agent import ReactAgent, ToolRegistry, ToolSchema
from tools import (
    # Examples
    run_pytest_on_directory,
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

app = FastAPI(
    title="React Agent API",
    description="API for interacting with the React Agent",
    version="1.0.0",
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tool registry and register tools
tool_registry = ToolRegistry()

tool_registry.register_tool(
    "run_pytest_on_directory",
    run_pytest_on_directory,
    "Run pytest inside a student submission directory and return structured results",
    {
        "type": "object",
        "properties": {
            "directory_path": {"type": "string"}
        },
        "required": ["directory_path"]
    }
)

tool_registry.register_tool(
    "load_rubric",
    load_rubric,
    "Load a grading rubric from a JSON file",
    {
        "type": "object",
        "properties": {
            "rubric_path": {"type": "string"},
            "rubric": {"type": "object"},
            "selected_ids": {"type": "array", "items": {"type": "string"}},
        },
        "anyOf": [
            {"required": ["rubric"]},
            {"required": ["rubric_path"]}
        ],
    },
)

tool_registry.register_tool(
    "list_repo_files",
    list_repo_files,
    "List all files inside a cloned student repository",
    {
        "type": "object",
        "properties": {
            "repo_path": {"type": "string"}
        },
        "required": ["repo_path"]
    }
)


tool_registry.register_tool(
    "load_submission",
    load_submission,
    "Load a student's Python submission file",
    {
        "type": "object",
        "properties": {
            "submission_path": {"type": "string"},
        },
        "required": ["submission_path"],
    },
)

tool_registry.register_tool(
    "load_test_cases",
    load_test_cases,
    "Load test cases from JSON file",
    {
        "type": "object",
        "properties": {
            "test_cases_path": {"type": "string"},
        },
        "required": ["test_cases_path"],
    },
)

tool_registry.register_tool(
    "load_test_cases",
    load_test_cases,
    "Load test cases from JSON file",
    {
        "type": "object",
        "properties": {
            "test_cases_path": {"type": "string"},
        },
        "required": ["test_cases_path"],
    },
)

tool_registry.register_tool(
    "check_syntax",
    check_syntax,
    "Check syntax validity of Python code",
    {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "repo_path": {"type": "string"},
        },
        "anyOf": [
            {"required": ["code"]},
            {"required": ["repo_path"]}
        ],
    },
)

tool_registry.register_tool(
    "check_required_elements",
    check_required_elements,
    "Check required functions/classes exist in the code",
    {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "repo_path": {"type": "string"},
            "required_items": {"type": "array", "items": {"type": "string"}},
        },
        "anyOf": [
            {"required": ["code", "required_items"]},
            {"required": ["repo_path", "required_items"]}
        ],
    },
)

tool_registry.register_tool(
    "check_documentation_tools",
    check_documentation_tools,
    "Check documentation and docstring completeness",
    {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "repo_path": {"type": "string"},
        },
        "anyOf": [
            {"required": ["code"]},
            {"required": ["repo_path"]}
        ],
    },
)

tool_registry.register_tool(
    "check_style_tools",
    check_style_tools,
    "Check code style quality",
    {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "repo_path": {"type": "string"},
        },
        "anyOf": [
            {"required": ["code"]},
            {"required": ["repo_path"]}
        ],
    },
)

tool_registry.register_tool(
    "run_functional_tests",
    run_functional_tests,
    "Run functional test cases on student code",
    {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "test_cases": {"type": "array"}
        },
        "required": ["code", "test_cases"],
    },
)

tool_registry.register_tool(
    "compute_final_grade",
    compute_final_grade,
    "Compute the final grade from all grading components",
    {
        "type": "object",
        "properties": {
            "rubric": {"type": "object"},
            "syntax": {"type": "object"},
            "required": {"type": "object"},
            "documentation": {"type": "object"},
            "style": {"type": "object"},
            "tests": {"type": "object"},
        },
        "required": ["rubric", "syntax", "required", "documentation", "style", "tests"],
    },
)

# Initialize agent
agent = ReactAgent(tool_registry, max_iterations=10)


class TaskRequest(BaseModel):
    """Request model for running a task."""

    task: str
    context: Dict[str, Any]
    max_iterations: Optional[int] = 10


class ToolExecutionRequest(BaseModel):
    """Request model for executing a specific tool."""

    tool_name: str
    parameters: Dict[str, Any]


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "React Agent API",
        "version": "1.0.0",
        "endpoints": {"tools": "/tools", "run": "/run", "execute": "/execute"},
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/tools", response_model=list[ToolSchema])
async def list_tools():
    """List all available tools."""
    return tool_registry.list_tools()


@app.get("/tools/{tool_name}", response_model=ToolSchema)
async def get_tool_schema(tool_name: str):
    """Get schema for a specific tool."""
    schema = tool_registry.get_schema(tool_name)
    if schema is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return schema


## run helper function:
async def run_single_rubric_item(tool_registry, rubric_item_id, rubric_map, repo_path, max_iterations):
    start = time.time()

    # Build a prompt specifically for this item
    item = rubric_map[rubric_item_id]
    description = item.get("description", "")

    task_prompt = (
        f"Grade the student submission based on the rubric item '{rubric_item_id}'.\n"
        f"Description: {description}\n"
        f"Submission files are located at: {repo_path}"
    )

    context = {
        "rubric_items": [rubric_item_id],
        "rubric": {rubric_item_id: item},
        "repo_path": repo_path,
    }

    # NEW AGENT instance for this one rubric item
    local_agent = ReactAgent(tool_registry, max_iterations=max_iterations)

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: local_agent.run(task_prompt, context)
    )

    return {
        "rubric_item": rubric_item_id,
        "result": result.return_values,
        "log": result.log,
        "steps": [
            {
                "action": {
                    "tool": step.action.tool,
                    "input": step.action.tool_input,
                    "log": step.action.log,
                },
                "observation": step.observation,
            }
            for step in local_agent.get_intermediate_steps()
        ],
        "duration": time.time() - start,
    }

@app.post("/run")
async def run_agent(request: TaskRequest):
    """
    Multi-agent version of /run:
    - Creates a new agent per rubric item
    - Runs them concurrently
    - Returns a list of per-item results
    """

    print("RUNNING REQUEST BODY:", request.dict())

    rubric_item_ids = request.context.get("rubric_items", [])
    rubric_map = request.context.get("rubric", {})
    repo_path = request.context.get("repo_path")
    max_iter = request.max_iterations or 10

    if not rubric_item_ids:
        raise HTTPException(status_code=400, detail="Missing rubric items")

    # Create concurrent tasks
    tasks = [
        run_single_rubric_item(
            tool_registry,
            rubric_item_id,
            rubric_map,
            repo_path,
            max_iter
        )
        for rubric_item_id in rubric_item_ids
    ]

    try:
        # Run all rubric-item agents concurrently
        results = await asyncio.gather(*tasks)

        return {
            "multi_agent_results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running multi-agent task: {str(e)}")



@app.post("/execute")
async def execute_tool(request: ToolExecutionRequest):
    """Execute a specific tool directly."""
    print("EXECUTING TOOL REQUEST BODY:", request.dict())
    tool = tool_registry.get_tool(request.tool_name)
    if tool is None:
        raise HTTPException(
            status_code=404, detail=f"Tool '{request.tool_name}' not found"
        )

    try:
        result = tool(**request.parameters)
        return {"tool": request.tool_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing tool: {str(e)}")


@app.get("/discover")
async def discover_tools():
    """Discover all available tools with their schemas."""
    return tool_registry.discover_tools()


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept rubric JSON → parse → return structured rubric items"""

    # load raw JSON
    raw = await file.read()
    print(f"RECEIVED RUBRIC: {file}")
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    
    # convert into structured RubricSchema
    rubric_items=[]
    total_points=0

    for key, value in data.items():
        item = RubricItem(
            id=key,
            label=key.replace("_", " ").title(),
            description=value.get("description", ""),
            max_points=value.get("points", 0),
            type="required_elements" if "items" in value else "general",
            items=value.get("items", None)
        )
        rubric_items.append(item)
        total_points += item.max_points
        
    rubric_schema = RubricSchema(
        rubric_items=rubric_items,
        total_points=total_points
    )
    
    return rubric_schema

@app.post("/upload-github")
async def upload_github_repo(payload: dict = Body(...)):
    """
    Accepts a GitHub repository URL, clones it, and returns local project path.
    """

    url = payload.get("url")
    print("RECEIVED GITHUB URL:", url)

    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="Missing repository URL")

    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # Temporary storage
    temp_dir = tempfile.mkdtemp()

    try:
        print("CLONING REPOSITORY INTO:", temp_dir)
        Repo.clone_from(url, temp_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clone repository: {str(e)}")

    return {
        "status": "cloned",
        "project_path": temp_dir,
        "url": url
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)