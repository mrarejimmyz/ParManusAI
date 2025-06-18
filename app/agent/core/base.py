"""
Unified Agent Core - Single Base Class for All Agents
Eliminates duplication across 5+ agent base implementations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from app.config import config
from app.llm import LLM
from app.logger import logger
from app.memory import Memory
from app.schema import AgentState, Message


class AgentCapability(str, Enum):
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
    INTERACTION = "interaction"
    LEARNING = "learning"


class AgentConfig(BaseModel):
    """Unified configuration for all agent types."""

    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    capabilities: List[AgentCapability] = Field(
        default_factory=list, description="Agent capabilities"
    )
    max_steps: int = Field(default=30, description="Maximum execution steps")
    max_observe: Optional[int] = Field(
        default=None, description="Maximum observation length"
    )
    system_prompt: Optional[str] = Field(
        default=None, description="System prompt template"
    )
    next_step_prompt: Optional[str] = Field(
        default=None, description="Next step prompt template"
    )
    tools: List[str] = Field(default_factory=list, description="Available tool names")
    memory_enabled: bool = Field(default=True, description="Enable memory system")
    learning_enabled: bool = Field(default=False, description="Enable learning system")


class BaseAgent(BaseModel, ABC):
    """
    Unified base class for all agents.

    Replaces all existing agent base classes with a single, consistent interface.
    Provides capability-driven architecture where agents are defined by what they can do.
    """

    # Core configuration
    config: AgentConfig = Field(..., description="Agent configuration")

    # Core dependencies
    llm: LLM = Field(default_factory=LLM, description="Language model instance")
    memory: Optional[Memory] = Field(default=None, description="Memory system")

    # Execution state
    state: AgentState = Field(
        default=AgentState.IDLE, description="Current execution state"
    )
    current_step: int = Field(default=0, description="Current step number")
    messages: List[Message] = Field(
        default_factory=list, description="Conversation history"
    )

    # Execution results
    last_result: Optional[str] = Field(
        default=None, description="Last execution result"
    )
    execution_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Execution history"
    )

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize memory if enabled
        if self.config.memory_enabled and not self.memory:
            self.memory = Memory()

        # Set initial state
        self.state = AgentState.IDLE

        logger.info(
            f"🤖 Initialized {self.config.name} with capabilities: {[c.value for c in self.config.capabilities]}"
        )

    # Abstract methods that subclasses must implement
    @abstractmethod
    async def think(self) -> bool:
        """
        Think about the next action to take.

        Returns:
            bool: True if thinking was successful and agent should continue
        """
        pass

    @abstractmethod
    async def act(self) -> str:
        """
        Execute the planned action.

        Returns:
            str: Result of the action
        """
        pass

    # Core execution framework
    async def step(self) -> str:
        """
        Execute a single step of the agent's workflow.

        Returns:
            str: Result of the step
        """
        if self.state == AgentState.FINISHED:
            return "Agent has finished execution"

        if self.current_step >= self.config.max_steps:
            self.state = AgentState.FINISHED
            return f"Maximum steps ({self.config.max_steps}) reached"

        try:
            self.state = AgentState.THINKING
            self.current_step += 1

            # Think about next action
            should_continue = await self.think()

            if not should_continue:
                self.state = AgentState.FINISHED
                return "Agent decided to stop"

            # Execute action
            self.state = AgentState.ACTING
            result = await self.act()

            # Store result
            self.last_result = result
            self.execution_history.append(
                {
                    "step": self.current_step,
                    "timestamp": __import__("time").time(),
                    "result": result,
                }
            )

            # Check if finished
            if self.state != AgentState.FINISHED:
                self.state = AgentState.IDLE

            return result

        except Exception as e:
            logger.error(f"Error in {self.config.name} step {self.current_step}: {e}")
            self.state = AgentState.FINISHED
            return f"Error: {str(e)}"

    async def run(self, request: Optional[str] = None) -> str:
        """
        Run the agent until completion.

        Args:
            request: Optional initial request

        Returns:
            str: Final result
        """
        if request:
            await self.add_user_message(request)

        results = []

        while (
            self.state != AgentState.FINISHED
            and self.current_step < self.config.max_steps
        ):
            result = await self.step()
            results.append(result)

            # Break if we get an error or completion signal
            if "Error:" in result or "finished" in result.lower():
                break

        final_result = results[-1] if results else "No steps executed"
        logger.info(f"🏁 {self.config.name} completed after {self.current_step} steps")

        return final_result

    # Capability checking
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.config.capabilities

    def has_capabilities(self, capabilities: List[AgentCapability]) -> bool:
        """Check if agent has all specified capabilities."""
        return all(cap in self.config.capabilities for cap in capabilities)

    def has_any_capability(self, capabilities: List[AgentCapability]) -> bool:
        """Check if agent has any of the specified capabilities."""
        return any(cap in self.config.capabilities for cap in capabilities)

    # Message management
    async def add_user_message(self, content: str):
        """Add a user message to the conversation."""
        message = Message(role="user", content=content)
        self.messages.append(message)

        if self.memory:
            await self.memory.add_message(message)

    async def add_assistant_message(self, content: str):
        """Add an assistant message to the conversation."""
        message = Message(role="assistant", content=content)
        self.messages.append(message)

        if self.memory:
            await self.memory.add_message(message)

    # State management
    def reset(self):
        """Reset the agent to initial state."""
        self.state = AgentState.IDLE
        self.current_step = 0
        self.messages = []
        self.last_result = None
        self.execution_history = []

        if self.memory:
            self.memory.clear()

        logger.info(f"🔄 Reset {self.config.name}")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "current_step": self.current_step,
            "max_steps": self.config.max_steps,
            "capabilities": [c.value for c in self.config.capabilities],
            "last_result": self.last_result,
            "message_count": len(self.messages),
        }


class SimpleAgent(BaseAgent):
    """Simple agent implementation for basic tasks."""

    def __init__(self, **kwargs):
        # Set default config if not provided
        if "config" not in kwargs:
            kwargs["config"] = AgentConfig(
                name="SimpleAgent",
                description="A simple agent for basic tasks",
                capabilities=[AgentCapability.REASONING, AgentCapability.TOOL_CALLING],
                max_steps=10,
            )
        super().__init__(**kwargs)

    async def think(self) -> bool:
        """Simple thinking: always continue unless finished."""
        if not self.messages:
            return False

        # Get the last user message
        user_messages = [msg for msg in self.messages if msg.role == "user"]
        if not user_messages:
            return False

        return True

    async def act(self) -> str:
        """Simple action: respond to the last user message."""
        user_messages = [msg for msg in self.messages if msg.role == "user"]
        if not user_messages:
            return "No user message to respond to"

        last_message = user_messages[-1].content

        # Use LLM to generate response
        try:
            response = await self.llm.ask(
                f"Please respond to this request: {last_message}"
            )

            await self.add_assistant_message(response)
            self.state = AgentState.FINISHED

            return response

        except Exception as e:
            return f"Error generating response: {str(e)}"


class PlanningAgent(BaseAgent):
    """Agent specialized in task planning and organization."""

    def __init__(self, **kwargs):
        # Set default config if not provided
        if "config" not in kwargs:
            kwargs["config"] = AgentConfig(
                name="PlanningAgent",
                description="An agent specialized in task planning and organization",
                capabilities=[
                    AgentCapability.REASONING,
                    AgentCapability.PLANNING,
                    AgentCapability.TASK_AUTOMATION,
                ],
                max_steps=20,
            )
        super().__init__(**kwargs)

        self.current_plan: Optional[Dict] = None

    async def think(self) -> bool:
        """Planning-focused thinking."""
        if not self.messages:
            return False

        # Check if we need to create a plan
        if not self.current_plan:
            return True

        # Check if plan is complete
        return not self._is_plan_complete()

    async def act(self) -> str:
        """Planning-focused action."""
        if not self.current_plan:
            return await self._create_plan()
        else:
            return await self._execute_plan_step()

    async def _create_plan(self) -> str:
        """Create a task plan."""
        user_messages = [msg for msg in self.messages if msg.role == "user"]
        if not user_messages:
            return "No task to plan"

        task = user_messages[-1].content

        try:
            planning_prompt = f"""
            Create a detailed plan for the following task: {task}

            Break it down into specific, actionable steps.
            Format as a JSON structure with phases and steps.
            """

            plan_text = await self.llm.ask(planning_prompt)

            # Store the plan (simplified for now)
            self.current_plan = {
                "task": task,
                "plan_text": plan_text,
                "completed": False,
            }

            await self.add_assistant_message(f"Created plan: {plan_text}")

            return f"Plan created for: {task}"

        except Exception as e:
            return f"Error creating plan: {str(e)}"

    async def _execute_plan_step(self) -> str:
        """Execute the next step of the plan."""
        # Simplified execution - mark as complete
        self.current_plan["completed"] = True
        self.state = AgentState.FINISHED

        return "Plan execution completed"

    def _is_plan_complete(self) -> bool:
        """Check if the current plan is complete."""
        return self.current_plan and self.current_plan.get("completed", False)


# Agent factory for creating specialized agents
class AgentFactory:
    """Factory for creating specialized agent instances."""

    @staticmethod
    def create_agent(agent_type: str, **kwargs) -> BaseAgent:
        """
        Create an agent of the specified type.

        Args:
            agent_type: Type of agent to create
            **kwargs: Additional configuration

        Returns:
            BaseAgent: The created agent instance
        """
        agent_type = agent_type.lower()

        if agent_type == "simple":
            return SimpleAgent(**kwargs)
        elif agent_type == "planning" or agent_type == "planner":
            return PlanningAgent(**kwargs)
        else:
            # Default to simple agent
            logger.warning(f"Unknown agent type '{agent_type}', creating SimpleAgent")
            return SimpleAgent(**kwargs)

    @staticmethod
    def create_capable_agent(
        capabilities: List[AgentCapability], name: str = "CapableAgent", **kwargs
    ) -> BaseAgent:
        """
        Create an agent with specific capabilities.

        Args:
            capabilities: List of required capabilities
            name: Agent name
            **kwargs: Additional configuration

        Returns:
            BaseAgent: Agent with specified capabilities
        """
        config = AgentConfig(
            name=name,
            description=f"Agent with capabilities: {[c.value for c in capabilities]}",
            capabilities=capabilities,
            **kwargs,
        )

        # Choose appropriate base class based on capabilities
        if AgentCapability.PLANNING in capabilities:
            return PlanningAgent(config=config)
        else:
            return SimpleAgent(config=config)


# Backward compatibility exports
def create_agent(agent_type: str, **kwargs) -> BaseAgent:
    """Backward compatibility function."""
    return AgentFactory.create_agent(agent_type, **kwargs)


__all__ = [
    "BaseAgent",
    "SimpleAgent",
    "PlanningAgent",
    "AgentFactory",
    "AgentConfig",
    "AgentCapability",
    "create_agent",
]
