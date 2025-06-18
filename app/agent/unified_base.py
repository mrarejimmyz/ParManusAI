"""
Unified Agent Architecture - Single Base for All Agent Types
Eliminates duplication across 12+ agent implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.config import config
from app.llm import LLM
from app.logger import logger
from app.memory import Memory
from app.schema import AgentState, Message
from app.tool import ToolCollection


class AgentCapability:
    """Defines agent capabilities in a modular way."""

    # Core capabilities
    REASONING = "reasoning"
    PLANNING = "planning"
    BROWSING = "browsing"
    CODING = "coding"
    FILE_OPS = "file_operations"
    SEARCH = "search"
    VISION = "vision"
    TOOL_CALLING = "tool_calling"
    MEMORY = "memory"

    # Specialized capabilities
    DATA_ANALYSIS = "data_analysis"
    WEB_SCRAPING = "web_scraping"
    REPORT_GENERATION = "report_generation"
    TASK_AUTOMATION = "task_automation"


class AgentConfig(BaseModel):
    """Unified configuration for all agent types."""

    name: str
    description: str
    capabilities: List[str] = Field(default_factory=list)
    max_steps: int = Field(default=50)
    max_observe: int = Field(default=10)
    enable_memory: bool = Field(default=True)
    enable_tools: bool = Field(default=True)
    system_prompt: Optional[str] = None
    specialized_tools: List[str] = Field(default_factory=list)


class BaseAgent(BaseModel, ABC):
    """
    Unified base agent that all other agents inherit from.
    Provides consistent LLM integration, memory, and tool management.
    """

    # Configuration
    config: AgentConfig

    # Core components (initialized automatically)
    llm: Optional[LLM] = None
    memory: Optional[Memory] = None
    tools: Optional[ToolCollection] = None

    # State management
    state: AgentState = Field(default=AgentState.IDLE)
    current_step: int = Field(default=0)

    # Execution tracking
    last_action: Optional[str] = None
    last_result: Optional[str] = None
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)

    def __init__(self, **kwargs):
        """Initialize unified agent with automatic component setup."""
        super().__init__(**kwargs)

        # Initialize LLM if not provided
        if self.llm is None:
            self.llm = LLM()

        # Initialize memory if enabled
        if self.config.enable_memory and self.memory is None:
            self.memory = Memory()

        # Initialize tools if enabled
        if self.config.enable_tools and self.tools is None:
            self.tools = self._create_tool_collection()

        logger.info(
            f"🤖 Initialized {self.config.name} agent with capabilities: {self.config.capabilities}"
        )

    def _create_tool_collection(self) -> ToolCollection:
        """Create tool collection based on agent capabilities."""
        from app.tool import ToolCollection
        from app.tool.ask_human import AskHuman
        from app.tool.browser_use_tool import BrowserUseTool
        from app.tool.python_execute import PythonExecute
        from app.tool.terminate import Terminate

        tools = []

        # Add core tools based on capabilities
        if AgentCapability.CODING in self.config.capabilities:
            tools.append(PythonExecute())

        if AgentCapability.BROWSING in self.config.capabilities:
            tools.append(BrowserUseTool())

        # Always include basic tools
        tools.extend([AskHuman(), Terminate()])

        # Add specialized tools
        for tool_name in self.config.specialized_tools:
            tool_class = self._get_tool_class(tool_name)
            if tool_class:
                tools.append(tool_class())

        return ToolCollection(*tools)

    def _get_tool_class(self, tool_name: str):
        """Get tool class by name."""
        tool_mapping = {
            "web_search": "app.tool.web_search.WebSearch",
            "str_replace": "app.tool.str_replace_editor.StrReplaceEditor",
            "bash": "app.tool.bash.Bash",
            # Add more as needed
        }

        if tool_name in tool_mapping:
            module_path, class_name = tool_mapping[tool_name].rsplit(".", 1)
            try:
                module = __import__(module_path, fromlist=[class_name])
                return getattr(module, class_name)
            except ImportError:
                logger.warning(f"Could not import tool: {tool_name}")

        return None

    def update_memory(self, role: str, content: str):
        """Update agent memory with message."""
        if self.memory:
            message = Message(role=role, content=content)
            self.memory.add_message(message)

    def get_system_prompt(self) -> str:
        """Get system prompt for the agent."""
        if self.config.system_prompt:
            return self.config.system_prompt

        # Generate default system prompt based on capabilities
        capabilities_desc = ", ".join(self.config.capabilities)
        return f"""You are {self.config.name}, {self.config.description}

Your capabilities include: {capabilities_desc}

You can use various tools to accomplish tasks. Always think step by step and explain your reasoning.
"""

    async def think(self) -> bool:
        """Core thinking/reasoning method - implemented by specific agents."""
        # Default implementation - can be overridden
        if self.current_step >= self.config.max_steps:
            logger.warning(f"Agent reached max steps ({self.config.max_steps})")
            self.state = AgentState.FINISHED
            return False

        return await self._execute_reasoning_step()

    @abstractmethod
    async def _execute_reasoning_step(self) -> bool:
        """Execute one reasoning step - must be implemented by specific agents."""
        pass

    async def step(self) -> str:
        """Execute one agent step."""
        self.current_step += 1

        try:
            result = await self.think()

            if result:
                self.last_result = "Step completed successfully"
                return self.last_result
            else:
                self.last_result = "Step failed or agent finished"
                return self.last_result

        except Exception as e:
            error_msg = f"Error in step {self.current_step}: {str(e)}"
            logger.error(error_msg)
            self.last_result = error_msg
            return error_msg

    async def run(self) -> str:
        """Run the agent until completion."""
        self.state = AgentState.RUNNING

        while self.state == AgentState.RUNNING:
            result = await self.step()

            # Check if agent should stop
            if self.state in [AgentState.FINISHED, AgentState.ERROR]:
                break

        return self.last_result or "Agent execution completed"


class SimpleAgent(BaseAgent):
    """Simple agent for basic tasks without complex planning."""

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="SimpleAgent",
            description="A simple agent for basic tasks",
            capabilities=[AgentCapability.REASONING, AgentCapability.TOOL_CALLING],
            max_steps=10,
        )
        super().__init__(config=config, **kwargs)

    async def _execute_reasoning_step(self) -> bool:
        """Simple reasoning - just respond to user queries."""
        if not self.memory or not self.memory.messages:
            self.state = AgentState.FINISHED
            return False

        # Get the last user message
        user_messages = [msg for msg in self.memory.messages if msg.role == "user"]
        if not user_messages:
            self.state = AgentState.FINISHED
            return False

        last_query = user_messages[-1].content

        # Generate response using LLM
        system_prompt = self.get_system_prompt()
        response = await self.llm.ask(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": last_query},
            ]
        )

        # Update memory with response
        self.update_memory("assistant", response)

        # Mark as finished
        self.state = AgentState.FINISHED
        return True


class PlanningAgent(BaseAgent):
    """Agent specialized in task planning and organization."""

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="PlanningAgent",
            description="An agent specialized in creating and managing task plans",
            capabilities=[
                AgentCapability.REASONING,
                AgentCapability.PLANNING,
                AgentCapability.TOOL_CALLING,
            ],
            max_steps=20,
            specialized_tools=["str_replace"],
        )
        super().__init__(config=config, **kwargs)

    async def _execute_reasoning_step(self) -> bool:
        """Planning-focused reasoning step."""
        # Implementation would go here - this is a template
        # In a real implementation, this would handle task breakdown,
        # plan creation, progress tracking, etc.

        self.state = AgentState.FINISHED
        return True


# Agent factory for creating specialized agents
class AgentFactory:
    """Factory for creating specialized agent instances."""

    @staticmethod
    def create_agent(agent_type: str, **kwargs) -> BaseAgent:
        """Create agent by type."""
        agent_classes = {
            "simple": SimpleAgent,
            "planning": PlanningAgent,
            # Add more as implemented
        }

        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")

        return agent_classes[agent_type](**kwargs)

    @staticmethod
    def create_custom_agent(config: AgentConfig, **kwargs) -> BaseAgent:
        """Create custom agent with specific configuration."""

        class CustomAgent(BaseAgent):
            def __init__(self, **init_kwargs):
                super().__init__(config=config, **init_kwargs)

            async def _execute_reasoning_step(self) -> bool:
                # Default implementation
                self.state = AgentState.FINISHED
                return True

        return CustomAgent(**kwargs)


# Backward compatibility exports
__all__ = [
    "BaseAgent",
    "SimpleAgent",
    "PlanningAgent",
    "AgentFactory",
    "AgentConfig",
    "AgentCapability",
]
