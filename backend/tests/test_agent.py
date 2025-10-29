"""Unit tests for the React Agent."""

import pytest
from backend.agent import ReactAgent, ToolRegistry, AgentAction, AgentFinish, AgentStep, ToolSchema


def sample_tool(message: str) -> str:
    """A sample tool for testing."""
    return f"Processed: {message}"


def calculator_tool(a: int, b: int) -> int:
    """A calculator tool for testing."""
    return a + b


class TestToolRegistry:
    """Test cases for ToolRegistry."""
    
    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        registry.register_tool(
            "sample",
            sample_tool,
            "A sample tool"
        )
        
        assert registry.get_tool("sample") is not None
        assert registry.get_schema("sample") is not None
    
    def test_register_tool_with_parameters(self):
        """Test registering a tool with explicit parameters."""
        registry = ToolRegistry()
        params = {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            },
            "required": ["message"]
        }
        registry.register_tool(
            "sample",
            sample_tool,
            "A sample tool",
            params
        )
        
        schema = registry.get_schema("sample")
        assert schema is not None
        assert schema.parameters == params
    
    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist."""
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent") is None
        assert registry.get_schema("nonexistent") is None
    
    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        registry.register_tool("tool1", sample_tool, "Tool 1")
        registry.register_tool("tool2", calculator_tool, "Tool 2")
        
        tools = registry.list_tools()
        assert len(tools) == 2
        assert all(isinstance(tool, ToolSchema) for tool in tools)
    
    def test_discover_tools(self):
        """Test discovering all tools."""
        registry = ToolRegistry()
        registry.register_tool("tool1", sample_tool, "Tool 1")
        registry.register_tool("tool2", calculator_tool, "Tool 2")
        
        discovered = registry.discover_tools()
        assert len(discovered) == 2
        assert "tool1" in discovered
        assert "tool2" in discovered
    
    def test_auto_generate_parameter_schema(self):
        """Test automatic parameter schema generation."""
        registry = ToolRegistry()
        registry.register_tool("calculator", calculator_tool, "Calculator")
        
        schema = registry.get_schema("calculator")
        assert schema is not None
        assert "properties" in schema.parameters
        assert "a" in schema.parameters["properties"]
        assert "b" in schema.parameters["properties"]
        assert schema.parameters["properties"]["a"]["type"] == "integer"
        assert schema.parameters["properties"]["b"]["type"] == "integer"


class TestReactAgent:
    """Test cases for ReactAgent."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        registry = ToolRegistry()
        agent = ReactAgent(registry, max_iterations=5)
        
        assert agent.tool_registry is registry
        assert agent.max_iterations == 5
        assert len(agent.intermediate_steps) == 0
    
    def test_execute_action(self):
        """Test executing an action."""
        registry = ToolRegistry()
        registry.register_tool("sample", sample_tool, "A sample tool")
        agent = ReactAgent(registry)
        
        action = AgentAction(
            tool="sample",
            tool_input={"message": "hello"},
            log="Testing sample tool"
        )
        
        observation = agent.execute(action)
        assert observation == "Processed: hello"
    
    def test_execute_nonexistent_tool(self):
        """Test executing a non-existent tool."""
        registry = ToolRegistry()
        agent = ReactAgent(registry)
        
        action = AgentAction(
            tool="nonexistent",
            tool_input={},
            log="Testing nonexistent tool"
        )
        
        observation = agent.execute(action)
        assert "Error" in observation
        assert "not found" in observation
    
    def test_execute_with_error(self):
        """Test executing a tool that raises an error."""
        registry = ToolRegistry()
        
        def error_tool():
            raise ValueError("Test error")
        
        registry.register_tool("error", error_tool, "Error tool")
        agent = ReactAgent(registry)
        
        action = AgentAction(
            tool="error",
            tool_input={},
            log="Testing error tool"
        )
        
        observation = agent.execute(action)
        assert "Error executing tool" in observation
        assert "Test error" in observation
    
    def test_should_continue(self):
        """Test should_continue logic."""
        registry = ToolRegistry()
        agent = ReactAgent(registry, max_iterations=3)
        
        # Should continue on normal observation
        assert agent.should_continue("normal observation", 0) is True
        
        # Should not continue at max iterations
        assert agent.should_continue("normal observation", 3) is False
        
        # Should not continue on completion
        assert agent.should_continue("task complete", 0) is False
        assert agent.should_continue("finished", 0) is False
    
    def test_run(self):
        """Test running the agent."""
        registry = ToolRegistry()
        registry.register_tool("sample", sample_tool, "A sample tool")
        agent = ReactAgent(registry, max_iterations=1)
        
        result = agent.run("test task")
        
        assert isinstance(result, AgentFinish)
        assert "output" in result.return_values
        assert "steps" in result.return_values
        assert len(agent.get_intermediate_steps()) > 0
    
    def test_get_intermediate_steps(self):
        """Test getting intermediate steps."""
        registry = ToolRegistry()
        registry.register_tool("sample", sample_tool, "A sample tool")
        agent = ReactAgent(registry, max_iterations=2)
        
        agent.run("test task")
        steps = agent.get_intermediate_steps()
        
        assert isinstance(steps, list)
        assert all(isinstance(step, AgentStep) for step in steps)


class TestModels:
    """Test cases for Pydantic models."""
    
    def test_tool_schema_model(self):
        """Test ToolSchema model."""
        schema = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"}
        )
        
        assert schema.name == "test_tool"
        assert schema.description == "A test tool"
        assert schema.parameters == {"type": "object"}
    
    def test_agent_action_model(self):
        """Test AgentAction model."""
        action = AgentAction(
            tool="test_tool",
            tool_input={"key": "value"},
            log="test log"
        )
        
        assert action.tool == "test_tool"
        assert action.tool_input == {"key": "value"}
        assert action.log == "test log"
    
    def test_agent_finish_model(self):
        """Test AgentFinish model."""
        finish = AgentFinish(
            return_values={"result": "success"},
            log="completed"
        )
        
        assert finish.return_values == {"result": "success"}
        assert finish.log == "completed"
    
    def test_agent_step_model(self):
        """Test AgentStep model."""
        action = AgentAction(
            tool="test_tool",
            tool_input={"key": "value"}
        )
        step = AgentStep(
            action=action,
            observation="observed result"
        )
        
        assert step.action == action
        assert step.observation == "observed result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
