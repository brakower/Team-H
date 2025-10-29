"""Unit tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from backend.agent import ToolRegistry
from backend.tools import calculator, string_analyzer
from main import app


client = TestClient(app)


class TestAPI:
    """Test cases for the API endpoints."""

    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_list_tools(self):
        """Test listing tools."""
        response = client.get("/tools")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check that tools have required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool

    def test_get_tool_schema(self):
        """Test getting a specific tool schema."""
        response = client.get("/tools/calculator")
        assert response.status_code == 200
        schema = response.json()
        assert schema["name"] == "calculator"
        assert "description" in schema
        assert "parameters" in schema

    def test_get_nonexistent_tool_schema(self):
        """Test getting schema for non-existent tool."""
        response = client.get("/tools/nonexistent")
        assert response.status_code == 404

    def test_execute_tool(self):
        """Test executing a tool."""
        response = client.post(
            "/execute",
            json={
                "tool_name": "calculator",
                "parameters": {"operation": "add", "a": 5, "b": 3},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "calculator"
        assert data["result"] == 8

    def test_execute_nonexistent_tool(self):
        """Test executing a non-existent tool."""
        response = client.post(
            "/execute", json={"tool_name": "nonexistent", "parameters": {}}
        )
        assert response.status_code == 404

    def test_run_agent(self):
        """Test running the agent."""
        response = client.post(
            "/run", json={"task": "perform calculation", "max_iterations": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "log" in data
        assert "steps" in data
        assert isinstance(data["steps"], list)

    def test_discover_tools(self):
        """Test discovering tools."""
        response = client.get("/discover")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, dict)
        assert len(tools) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
