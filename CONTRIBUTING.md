# Contributing to Team-H

Thank you for your interest in contributing to Team-H! This guide will help you get started.

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20.x+
- Poetry (Python dependency manager)
- Git

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/brakower/Team-H.git
   cd Team-H
   ```

2. **Set up the backend:**
   ```bash
   cd backend
   poetry install
   ```

3. **Set up the frontend:**
   ```bash
   cd frontend
   npm install
   ```

## Development Workflow

### Backend Development

1. **Activate Poetry shell:**
   ```bash
   cd backend
   poetry shell
   ```

2. **Make your changes** to the Python code

3. **Format your code:**
   ```bash
   poetry run black backend/ tests/ main.py
   ```

4. **Run tests:**
   ```bash
   poetry run pytest
   ```

5. **Run the development server:**
   ```bash
   poetry run uvicorn main:app --reload
   ```

### Frontend Development

1. **Make your changes** to the Angular code

2. **Run the development server:**
   ```bash
   cd frontend
   ng serve
   ```

3. **Build the application:**
   ```bash
   ng build
   ```

## Code Style

### Python
- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 88)
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes

### TypeScript/Angular
- Follow Angular style guide
- Use TypeScript strict mode
- Write meaningful variable and function names
- Add JSDoc comments for complex functions

## Testing

### Backend Tests

All new features should include unit tests:

```python
# tests/test_my_feature.py
import pytest
from backend.my_module import my_function

def test_my_function():
    """Test description."""
    result = my_function(input)
    assert result == expected_output
```

Run tests:
```bash
poetry run pytest -v
```

### Frontend Tests

```typescript
// component.spec.ts
it('should create', () => {
  expect(component).toBeTruthy();
});
```

Run tests:
```bash
ng test
```

## Adding New Tools

### 1. Create the Tool

Create your tool in `backend/backend/tools/`:

```python
def my_tool(param1: str, param2: int) -> dict:
    """Tool description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dictionary with results
    """
    # Implementation
    return {"result": "value"}
```

### 2. Register the Tool

Add to `backend/main.py`:

```python
from backend.tools.my_tools import my_tool

tool_registry.register_tool(
    "my_tool",
    my_tool,
    "Brief description",
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

### 3. Write Tests

Add tests in `backend/tests/test_tools.py`:

```python
def test_my_tool():
    """Test my_tool functionality."""
    result = my_tool("test", 42)
    assert result["result"] == "expected"
```

## Pull Request Process

1. **Create a new branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes** and commit:
   ```bash
   git add .
   git commit -m "Add my new feature"
   ```

3. **Push to your fork:**
   ```bash
   git push origin feature/my-new-feature
   ```

4. **Create a Pull Request** on GitHub

5. **Ensure all checks pass:**
   - All tests pass
   - Code is formatted correctly
   - No linting errors

## Commit Message Guidelines

Follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
```
Add calculator tool with basic operations

- Implement add, subtract, multiply, divide
- Add comprehensive unit tests
- Update documentation

Fixes #123
```

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests added for new features
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages are clear and descriptive

## Development Container

For the best development experience, use the provided development container:

1. **Install Docker** and **VS Code**
2. **Install** the "Dev Containers" extension in VS Code
3. **Open** the project in VS Code
4. **Press** F1 and select "Dev Containers: Reopen in Container"

The container includes:
- Python 3.11
- Node.js 20.x
- Poetry
- All required tools and extensions

## Questions?

If you have questions, please:
1. Check the README.md
2. Check existing issues
3. Create a new issue with the "question" label

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to Team-H! 🎉
