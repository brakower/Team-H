"""React Agent implementation with main agent loop, tool discovery, and JSON Schema annotations."""

from typing import List, Dict, Any, Optional, Callable
from fastapi import Depends
from backend.models.tool_schema import ToolSchema
from backend.models.agent_action import AgentAction, AgentStep, AgentFinish
from backend.services.openai import OpenAIService, openai_client
import json
import inspect

class ToolRegistry:
    """Registry for discovering and managing tools."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, ToolSchema] = {}

    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a tool with the registry.

        Args:
            name: Name of the tool
            func: Callable function that implements the tool
            description: Description of what the tool does
            parameters: JSON Schema for the tool's parameters
        """
        self._tools[name] = func

        # Auto-generate parameter schema from function signature if not provided
        if parameters is None:
            parameters = self._generate_parameter_schema(func)

        schema = ToolSchema(
            name=name,
            description=description or func.__doc__ or "",
            parameters=parameters,
        )
        self._schemas[name] = schema

    def _generate_parameter_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate JSON Schema from function signature.

        Args:
            func: Function to generate schema for

        Returns:
            JSON Schema for the function's parameters
        """
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_schema = {"type": "string"}  # Default type

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                annotation = param.annotation
                if annotation == int:
                    param_schema["type"] = "integer"
                elif annotation == float:
                    param_schema["type"] = "number"
                elif annotation == bool:
                    param_schema["type"] = "boolean"
                elif annotation == list or annotation == List:
                    param_schema["type"] = "array"
                elif annotation == dict or annotation == Dict:
                    param_schema["type"] = "object"

            properties[param_name] = param_schema

            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {"type": "object", "properties": properties, "required": required}

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool by name.

        Args:
            name: Name of the tool

        Returns:
            The tool function or None if not found
        """
        return self._tools.get(name)

    def get_schema(self, name: str) -> Optional[ToolSchema]:
        """Get a tool schema by name.

        Args:
            name: Name of the tool

        Returns:
            The tool schema or None if not found
        """
        return self._schemas.get(name)

    def list_tools(self) -> List[ToolSchema]:
        """List all registered tools.

        Returns:
            List of all tool schemas
        """
        return list(self._schemas.values())

    def discover_tools(self) -> Dict[str, ToolSchema]:
        """Discover all available tools.

        Returns:
            Dictionary mapping tool names to their schemas
        """
        return self._schemas.copy()


class ReactAgent:
    """React Agent with ReAct (Reasoning and Acting) pattern.

    The agent follows a loop:
    1. Thought: Think about what to do
    2. Action: Execute a tool
    3. Observation: Observe the result
    4. Repeat until task is complete
    """

    def __init__(self, tool_registry: ToolRegistry, max_iterations: int = 10):
        """Initialize the React Agent.

        Args:
            tool_registry: Registry containing available tools
            max_iterations: Maximum number of iterations to prevent infinite loops
        """
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.intermediate_steps: list[AgentStep] = []

    def prompt_llm(self, prompt: str, available_tools: list[ToolSchema], history: list[AgentStep]):
        openai_service = OpenAIService(client=openai_client())
        tools_json = json.dumps([tool.model_dump() for tool in available_tools], indent=2)

        history_text = "\n".join(
            [f"Step {i + 1}: Tool={step.action.tool}, Observation={step.observation}" for i, step in enumerate(history)]
        )
        system_prompt = (
            f"Previous tool calls and observations:\n{history_text}\n\n"
            f"You have access to the following tools:\n\n{tools_json}\n\n"

            # ------------------------------------------------------------
            # STRICT STEP ORDER FOR GRADING
            # ------------------------------------------------------------
            f"When grading Python code, you MUST call tools in the EXACT following order:\n"
            f"1. load_rubric\n"
            f"2. load_submission\n"
            f"3. check_syntax\n"
            f"4. check_required_elements\n"
            f"5. check_documentation_tools\n"
            f"6. check_style_tools\n"
            f"7. load_test_cases\n"
            f"8. run_functional_tests OR run_pytest_on_directory\n"
            f"9. compute_final_grade\n\n"

            # ------------------------------------------------------------
            # HISTORY AWARENESS AND NON-REPETITION
            # ------------------------------------------------------------
            f"You MUST use the previous tool calls listed above to decide your NEXT action.\n"
            f"NEVER call a tool again if it already appears in the history.\n\n"

            f"If load_rubric already appears in the history, DO NOT call it again.\n"
            f"If load_submission already appears in the history, DO NOT call it again.\n"
            f"If check_syntax already appears in the history, DO NOT call it again.\n"
            f"If check_required_elements already appears in the history, DO NOT call it again.\n"
            f"If check_documentation_tools already appears in the history, DO NOT call it again.\n"
            f"If check_style_tools already appears in the history, DO NOT call it again.\n"
            f"If load_test_cases already appears in the history, DO NOT call it again.\n"
            f"If functional tests have already been run, DO NOT run them again.\n"
            f"Only call compute_final_grade when ALL steps above exist in the history.\n"
            f"After compute_final_grade, STOP making tool calls.\n\n"

            # ------------------------------------------------------------
            # CRITICAL: CODE PASSING RULES
            # ------------------------------------------------------------
            f"When you pass code to ANY tool (check_syntax, check_required_elements, "
            f"check_documentation_tools, check_style_tools, run_functional_tests), "
            f"you MUST use EXACTLY the code string returned by load_submission.\n"
            f"- DO NOT modify, shorten, reformat, or alter the code in ANY way.\n"
            f"- DO NOT remove docstrings or comments.\n"
            f"- DO NOT change indentation.\n"
            f"- DO NOT strip header text.\n"
            f"- Copy the string EXACTLY as it appeared in the load_submission observation.\n\n"

            # ------------------------------------------------------------
            # TOOL PARAMETER STRICTNESS
            # ------------------------------------------------------------
            f"Each tool has a strict parameter schema. You MUST:\n"
            f"- Use ONLY the parameters defined in the tool's schema.\n"
            f"- NEVER invent new parameters.\n"
            f"- NEVER reuse parameters from other tools.\n"
            f"- NEVER modify parameter names.\n\n"

            # ------------------------------------------------------------
            # RESPONSE FORMAT
            # ------------------------------------------------------------
            f"Respond ONLY with a JSON OBJECT that INSTANTIATES the following schema:\n"
            f"{AgentAction.model_json_schema()}\n\n"

            f"Important rules:\n"
            f"- DO NOT return the schema.\n"
            f"- DO NOT describe the schema.\n"
            f"- DO NOT explain your thinking.\n"
            f"- DO NOT wrap the result in code blocks.\n"
            f"- DO NOT include commentary.\n"
            f"- ONLY return a JSON object matching the schema.\n\n"

            f"Example format (do NOT copy these values):\n"
            f"{{\n"
            f"  \"tool\": \"some_tool_name\",\n"
            f"  \"tool_input\": {{ \"param\": \"value\" }}\n"
            f"}}"
        )


        user_prompt = f"Prompt: {prompt}"

        result = openai_service.prompt(
            available_tools=available_tools,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=AgentAction,
        )
        return result
    
    def plan(self, 
             task: str, 
             context: Optional[Dict[str, Any]] = None,
             history: list[AgentStep] = None
            ) -> AgentAction:
        """Plan the next action based on the task and context.

        Args:
            task: The task to accomplish
            context: Additional context for planning

        Returns:
            The next action to take
        """
        openai_service = OpenAIService(client=openai_client())
        available_tools = self.tool_registry.list_tools()

        if not available_tools:
            raise ValueError("No tools available")

        # Use the first available tool as a simple strategy (currently only add implemented)
        # This would be where we call OpenAI 

        action = self.prompt_llm(
            prompt=task,
            available_tools=available_tools,
            history=history or []
        )
        
        if not isinstance(action, AgentAction):
            raise ValueError("The LLM did not return a valid AgentAction.")

        return action

    def execute(self, action: AgentAction) -> str:
        """Execute an action using the appropriate tool.

        Args:
            action: The action to execute

        Returns:
            Observation from executing the action
        """
        tool = self.tool_registry.get_tool(action.tool)

        if tool is None:
            return f"Error: Tool '{action.tool}' not found"

        try:
            result = tool(**action.tool_input)
            return str(result)
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def should_continue(self, observation: str, iteration: int) -> bool:
        """Determine if the agent should continue iterating.

        Args:
            observation: The latest observation
            iteration: Current iteration number

        Returns:
            True if should continue, False otherwise
        """
        # 1. Stop if max iterations reached
        if iteration >= self.max_iterations:
            return False

        # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        # COMPLETION LOGIC 
        # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

        # 2. Stop if final grade was already computed
        if "total_score" in observation.lower() or "final_grade" in observation.lower():
            return False

        # 3. Stop if observation contains a full rubric breakdown
        if "breakdown" in observation.lower() and "percentage" in observation.lower():
            return False

        # 5. Original keywords logic
        if "complete" in observation.lower() or "finished" in observation.lower():
            return False
        
        #6. Early exit with errors
        if "Error executing tool" in observation:
            return False

        return True

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentFinish:
        """Run the agent loop to accomplish a task.

        Args:
            task: The task to accomplish
            context: Additional context for the task

        Returns:
            AgentFinish with the final result
        """
        self.intermediate_steps = []
        iteration = 0

        while iteration < self.max_iterations:
            # Step 1: Plan the next action
            action = self.plan(task, context, history=self.intermediate_steps)
            print(f"ACTION: {action}")

            # Step 2: Execute the action
            observation = self.execute(action)
            print(f"OBS: {observation}")
            
            # Step 3: Record the step
            step = AgentStep(action=action, observation=observation)
            self.intermediate_steps.append(step)

            # Step 4: Check if should continue
            if not self.should_continue(observation, iteration):
                break

            iteration += 1

        # Return final result
        return AgentFinish(
            return_values={
                "output": (
                    self.intermediate_steps[-1].observation
                    if self.intermediate_steps
                    else "No steps executed"
                ),
                "steps": len(self.intermediate_steps),
            },
            log=f"Completed task '{task}' in {len(self.intermediate_steps)} steps",
        )

    def get_intermediate_steps(self) -> List[AgentStep]:
        """Get the intermediate steps taken by the agent.

        Returns:
            List of agent steps
        """
        return self.intermediate_steps
