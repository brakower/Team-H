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
        },
        "required": ["rubric_path"],
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
        },
        "required": ["code"],
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
            "required_items": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["code", "required_items"],
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
        },
        "required": ["code"],
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
        },
        "required": ["code"],
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


@app.post("/run")
async def run_agent(request: TaskRequest):
    """Run the agent with a task."""
    print("REQUEST BODY:", request.dict())
    try:
        # Create new agent with custom max_iterations if provided
        current_agent = ReactAgent(tool_registry, max_iterations=request.max_iterations)
        result = current_agent.run(request.task, request.context)

        return {
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
                for step in current_agent.get_intermediate_steps()
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
async def execute_tool(request: ToolExecutionRequest):
    """Execute a specific tool directly."""
    tool = tool_registry.get_tool(request.tool_name)
    if tool is None:
        raise HTTPException(
            status_code=404, detail=f"Tool '{request.tool_name}' not found"
        )

    try:
        result = tool(**request.parameters)
        return {"tool": request.tool_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/discover")
async def discover_tools():
    """Discover all available tools with their schemas."""
    return tool_registry.discover_tools()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


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