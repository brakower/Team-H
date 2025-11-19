# Team-H

A modern full-stack application featuring an Angular frontend and Python backend with a React Agent implementation.

## Project Structure

```
Team-H/
├── .devcontainer/          # Development container configuration
│   ├── devcontainer.json   # VS Code dev container settings
│   └── Dockerfile          # Container image with Python 3.11, Node.js, npm, and Poetry
├── backend/                # Python backend with React Agent
│   ├── backend/            # Main backend package
│   │   ├── agent/          # React Agent implementation
│   │   └── tools/          # Tool implementations
│   ├── tests/              # Unit tests
│   ├── main.py             # FastAPI application
│   ├── pyproject.toml      # Poetry configuration
│   └── poetry.lock         # Poetry lock file
└── frontend/               # Angular frontend
    ├── src/                # Source files
    │   ├── app/            # Angular application
    │   │   ├── components/ # UI components
    │   │   └── services/   # Services for backend integration
    │   └── ...
    ├── angular.json        # Angular configuration
    └── package.json        # npm dependencies
```

## Backend Features

The Python backend includes:

- **React Agent**: An advanced agent system implementing the ReAct (Reasoning and Acting) pattern
  - Main agent loop with iterative reasoning
  - Automatic tool discovery mechanism
  - JSON Schema annotations for all tools
  - Comprehensive unit tests

- **Tool System**: 
  - Tool registry for dynamic tool management
  - Built-in tools
  - Auto-generated parameter schemas
  
- **FastAPI REST API**:
  - `/tools` - List all available tools
  - `/tools/{tool_name}` - Get tool schema
  - `/run` - Run the agent with a task
  - `/execute` - Execute a specific tool
  - `/discover` - Discover all tools with schemas
  - `/health` - Health check endpoint

- **Dependencies** (managed with Poetry):
  - FastAPI for REST API
  - Pydantic for data validation
  - LangChain for agent framework
  - Pytest for testing

## Frontend Features

The Angular frontend includes:

- **Agent Demo Component**: Interactive UI for testing the React Agent
- **Agent Service**: TypeScript service for backend communication
- **Modern Angular**: Using latest Angular features with standalone components
- **HTTP Client**: Configured for backend API integration
- **Responsive Design**: Clean, modern UI with CSS styling

## Prerequisites

- Python 3.11 or higher
- Node.js 20.x or higher
- npm
- Poetry (Python dependency manager)

## Setup Instructions

### Option 1: Using Dev Container (Recommended)

1. Open the project in VS Code
2. Install the "Dev Containers" extension
3. Press `F1` and select "Dev Containers: Reopen in Container"
4. The container will automatically set up Python 3.11, Node.js, npm, and Poetry
5. Dependencies will be installed automatically via the `postCreateCommand`

### Option 2: Manual Setup

#### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Poetry if not already installed:
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

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Usage Instructions

### Running the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Run the FastAPI server:
   ```bash
   poetry run python main.py
   # or using uvicorn directly
   poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. The API will be available at `http://localhost:8000`
4. API documentation available at `http://localhost:8000/docs`

### Running the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start the development server:
   ```bash
   npm start
   # or
   ng serve
   ```

3. Open your browser and navigate to `http://localhost:4200`

### Running Both Together

For full integration testing, run both servers simultaneously:

**Terminal 1 (Backend):**
```bash
cd backend
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
ng serve
```

Access the application at `http://localhost:4200`, which will communicate with the backend at `http://localhost:8000`.

## Testing Instructions

### Backend Tests

Run all tests:
```bash
cd backend
poetry run pytest
```

Run tests with verbose output:
```bash
poetry run pytest -v
```

Run tests with coverage:
```bash
poetry run pytest --cov=backend tests/
```

Run specific test file:
```bash
poetry run pytest tests/test_agent.py -v
```

### Test Coverage

The backend includes comprehensive unit tests:
- **test_agent.py**: Tests for React Agent, ToolRegistry, and data models
- **test_tools.py**: Tests for all tool implementations
- **test_api.py**: Tests for FastAPI endpoints

### Frontend Tests

```bash
cd frontend
npm test
```

## API Examples

### List Available Tools
```bash
curl http://localhost:8000/tools
```

### Execute a Tool
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "calculator",
    "parameters": {
      "operation": "add",
      "a": 5,
      "b": 3
    }
  }'
```

### Run Agent Task
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "perform calculation",
    "max_iterations": 5
  }'
```

## Frontend-Backend Integration

The application demonstrates full-stack integration:

1. **Angular Service** (`agent.ts`): Provides typed methods for all backend endpoints
2. **HTTP Communication**: Uses Angular's HttpClient with proper CORS configuration
3. **Data Models**: TypeScript interfaces matching backend Pydantic models
4. **Error Handling**: Comprehensive error handling on both frontend and backend
5. **Real-time Updates**: Interactive UI updates based on backend responses

### Example Integration Flow

1. User enters a task in the Angular UI
2. Angular service sends POST request to `/run` endpoint
3. Backend React Agent processes the task using available tools
4. Agent returns results with intermediate steps
5. Angular component displays the results with full execution trace

## Architecture

### Backend Architecture

- **React Agent Loop**: Implements the ReAct pattern (Thought → Action → Observation)
- **Tool Discovery**: Automatic discovery and registration of tools with JSON Schema
- **Modular Design**: Separate modules for agent logic, tools, and API
- **Type Safety**: Pydantic models for all data structures

### Frontend Architecture

- **Standalone Components**: Modern Angular architecture with standalone components
- **Service Layer**: Separation of concerns with dedicated API service
- **Reactive Programming**: RxJS observables for async operations
- **Component Communication**: Clean data flow from service to component to template

## Development Container

The `.devcontainer` folder provides a complete development environment:

- **Python 3.11**: Latest Python version with pip and virtual environment support
- **Node.js 20.x**: Latest LTS version of Node.js
- **npm**: Node package manager
- **Poetry**: Python dependency and package manager
- **VS Code Extensions**: Pre-configured extensions for Python and Angular development

## Configuration Files

- **pyproject.toml**: Python project configuration and dependencies
- **package.json**: Node.js dependencies and scripts
- **angular.json**: Angular CLI configuration
- **devcontainer.json**: Development container configuration

## Latest Package Versions

The project uses the latest stable versions of all dependencies:

**Backend:**
- FastAPI: ^0.120.1
- Pydantic: ^2.12.3
- LangChain: ^1.0.2
- Pytest: ^8.4.2
- Black: ^25.9.0
- Uvicorn: ^0.38.0

**Frontend:**
- Angular: Latest (generated via `ng new`)
- TypeScript: Latest stable
- RxJS: Latest stable

## License

This project is part of Team-H development.
