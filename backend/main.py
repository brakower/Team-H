"""FastAPI application for the React Agent backend."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from backend.agent import ReactAgent, ToolRegistry, ToolSchema
from backend.tools import calculator, string_analyzer, list_processor, json_formatter


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
    "calculator",
    calculator,
    "Perform basic arithmetic operations (add, subtract, multiply, divide)",
    {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
            },
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["operation", "a", "b"],
    },
)

tool_registry.register_tool(
    "string_analyzer",
    string_analyzer,
    "Analyze a string and return statistics",
    {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
)

tool_registry.register_tool(
    "list_processor",
    list_processor,
    "Process a list of items (count, sort, reverse, unique)",
    {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": {"type": "string"}},
            "operation": {
                "type": "string",
                "enum": ["count", "sort", "reverse", "unique"],
            },
        },
        "required": ["items", "operation"],
    },
)

tool_registry.register_tool(
    "json_formatter",
    json_formatter,
    "Format a dictionary as JSON",
    {
        "type": "object",
        "properties": {
            "data": {"type": "object"},
            "indent": {"type": "integer", "default": 2},
        },
        "required": ["data"],
    },
)

# Initialize agent
agent = ReactAgent(tool_registry, max_iterations=10)


class TaskRequest(BaseModel):
    """Request model for running a task."""

    task: str
    context: Optional[Dict[str, Any]] = None
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


@app.get("/tools", response_model=List[ToolSchema])
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
