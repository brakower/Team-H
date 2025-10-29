# Integration Example

This document provides a step-by-step example of how the Angular frontend integrates with the Python backend.

## Overview

The Team-H application demonstrates a complete full-stack integration where:
- The Angular frontend provides a user interface
- The Python backend exposes a REST API
- The React Agent processes tasks using registered tools

## Example Workflow

### 1. Frontend Service Layer

The `agent.ts` service in Angular provides typed methods for all backend endpoints:

```typescript
// Get available tools
this.agentService.getTools().subscribe(tools => {
  console.log('Available tools:', tools);
});

// Execute a specific tool
this.agentService.executeTool({
  tool_name: 'calculator',
  parameters: {
    operation: 'add',
    a: 5,
    b: 3
  }
}).subscribe(result => {
  console.log('Result:', result.result); // 8
});
```

### 2. Backend Processing

When the frontend sends a request to `/execute`:

```python
# main.py
@app.post("/execute")
async def execute_tool(request: ToolExecutionRequest):
    tool = tool_registry.get_tool(request.tool_name)
    result = tool(**request.parameters)
    return {"tool": request.tool_name, "result": result}
```

The backend:
1. Retrieves the tool from the registry
2. Executes it with the provided parameters
3. Returns the result in a JSON response

### 3. React Agent Execution

For more complex tasks, the frontend can use the React Agent:

```typescript
// Run the agent with a task
this.agentService.runAgent({
  task: 'analyze this text',
  max_iterations: 5
}).subscribe(result => {
  console.log('Agent log:', result.log);
  console.log('Steps taken:', result.steps);
  console.log('Final result:', result.result);
});
```

The agent follows a ReAct loop:
1. **Plan**: Determine which tool to use
2. **Execute**: Run the selected tool
3. **Observe**: Collect the result
4. **Repeat**: Continue until task is complete or max iterations reached

## Data Flow

```
User Input (Angular Component)
    ↓
Agent Service (TypeScript)
    ↓
HTTP Request
    ↓
FastAPI Endpoint (Python)
    ↓
React Agent / Tool Registry
    ↓
Tool Execution
    ↓
JSON Response
    ↓
Agent Service (TypeScript)
    ↓
Component Update (Angular)
    ↓
UI Display
```

## Example: Using the Calculator Tool

### Frontend Code:
```typescript
executeTool() {
  this.agentService.executeTool({
    tool_name: 'calculator',
    parameters: {
      operation: 'multiply',
      a: 6,
      b: 7
    }
  }).subscribe({
    next: (result) => {
      console.log('6 × 7 =', result.result); // 42
    },
    error: (err) => {
      console.error('Error:', err);
    }
  });
}
```

### Backend Processing:
```python
# tools/example_tools.py
def calculator(operation: str, a: float, b: float) -> float:
    operations = {
        "multiply": lambda x, y: x * y,
        # ... other operations
    }
    return operations[operation](a, b)
```

### Response:
```json
{
  "tool": "calculator",
  "result": 42
}
```

## Adding New Tools

### 1. Create the Tool (Backend)

```python
# backend/tools/custom_tools.py
def my_custom_tool(param1: str, param2: int) -> dict:
    """My custom tool description."""
    # Tool implementation
    return {"result": f"Processed {param1} {param2} times"}
```

### 2. Register the Tool (Backend)

```python
# main.py
tool_registry.register_tool(
    "my_custom_tool",
    my_custom_tool,
    "Description of what this tool does",
    {
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer"}
        },
        "required": ["param1", "param2"]
    }
)
```

### 3. Use the Tool (Frontend)

```typescript
// Component
this.agentService.executeTool({
  tool_name: 'my_custom_tool',
  parameters: {
    param1: 'hello',
    param2: 5
  }
}).subscribe(result => {
  console.log(result);
});
```

## JSON Schema Annotations

All tools are annotated with JSON Schema for validation and documentation:

```python
# Automatic schema generation from function signature
tool_registry.register_tool("example", example_func)

# Manual schema definition
tool_registry.register_tool(
    "example",
    example_func,
    "Description",
    {
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param"]
    }
)
```

The schemas are available via:
- `/tools` - List all tools with schemas
- `/tools/{name}` - Get specific tool schema
- `/discover` - Discover all tools

## Error Handling

### Frontend:
```typescript
this.agentService.runAgent(task).subscribe({
  next: (result) => {
    // Handle success
  },
  error: (err) => {
    // Handle HTTP errors
    console.error('API Error:', err.message);
  }
});
```

### Backend:
```python
@app.post("/execute")
async def execute_tool(request: ToolExecutionRequest):
    tool = tool_registry.get_tool(request.tool_name)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    try:
        result = tool(**request.parameters)
        return {"tool": request.tool_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing the Integration

### 1. Start the Backend:
```bash
cd backend
poetry run uvicorn main:app --reload --port 8000
```

### 2. Start the Frontend:
```bash
cd frontend
ng serve
```

### 3. Test in Browser:
- Navigate to `http://localhost:4200`
- Enter a task in the UI
- Click "Run Task"
- Observe the results

### 4. Test with cURL:
```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/tools

# Execute tool
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "calculator", "parameters": {"operation": "add", "a": 5, "b": 3}}'
```

## CORS Configuration

The backend is configured to allow requests from the Angular frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, update `allow_origins` to your production frontend URL.

## Summary

The integration demonstrates:
- ✅ Type-safe communication between frontend and backend
- ✅ React Agent with tool discovery and JSON Schema
- ✅ RESTful API design
- ✅ Error handling on both sides
- ✅ CORS configuration for cross-origin requests
- ✅ Comprehensive testing coverage
- ✅ Easy extensibility with new tools
