import os
import re
import sys
import time
import traceback
from typing import Any

from app.agent_router import route_agent
from app.agent_wrappers import create_agent
from app.config import Config, load_config
from app.logger import logger
from app.memory import Memory

# Conditional import for ParManus components
try:
    from app.llm import create_llm

    PARMANUS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ParManus components not fully available: {e}")
    PARMANUS_AVAILABLE = False


def initialize_system(args) -> tuple[Config, Any, Any]:
    """Initialize configuration, LLM, and memory."""
    logger.info("Initializing ParManus AI Agent System...")
    config = load_config(args.config if hasattr(args, "config") else None)

    if hasattr(args, "api_type") and args.api_type:
        if args.api_type != "ollama":
            logger.warning(
                f"Only Ollama is supported. Ignoring --api-type {args.api_type}"
            )
        # Note: api_type is now part of config.llm.api_type, not directly on config
        config.llm.api_type = "ollama"
    if hasattr(args, "workspace") and args.workspace:
        config.workspace_root = args.workspace
    if hasattr(args, "max_steps") and args.max_steps:
        config.max_steps = args.max_steps

    os.makedirs(config.workspace_root, exist_ok=True)

    try:
        # Pass the LLM settings instead of the entire config
        llm = create_llm(config.llm)
    except Exception as e:
        logger.error(f"Failed to initialize Ollama LLM: {e}")
        logger.error("Make sure Ollama is running: ollama serve")
        logger.error("And the model is available: ollama pull llama3.2-vision")
        sys.exit(1)

    # Pass specific memory settings from config
    memory = Memory(
        recover_last_session=(
            config.memory.recover_last_session if config.memory else False
        ),
        memory_compression=config.memory.memory_compression if config.memory else False,
    )
    return config, llm, memory


def display_startup_info(config: Config, args, parmanus_available: bool):
    """Display startup information."""
    logger.info("🚀 ParManus AI Agent System Ready!")
    logger.info(f"🧠 Backend: Ollama (Hybrid)")
    logger.info(f"🛠️ Tools Model: llama3.2")
    logger.info(f"👁️ Vision Model: llama3.2-vision")
    logger.info(f"📁 Workspace: {config.workspace_root}")
    if parmanus_available and not args.simple:
        logger.info("🛠️ Full tool system + vision available")
    else:
        logger.info("⚡ Simple mode active")


async def process_prompt(
    prompt: str, args, llm, config: Config, memory: Memory, parmanus_available: bool
):
    """Process a single user prompt."""
    if not prompt or not prompt.strip():
        return

    memory.push("user", prompt)

    try:
        agent_name = (
            args.agent
            if args.agent
            else route_agent(prompt, parmanus_available and not args.simple)
        )
        agent = create_agent(agent_name, llm, config)

        logger.info(f"🎯 Using {agent_name} agent...")

        start_time = time.time()
        result = await agent.run(prompt)
        end_time = time.time()

        memory.push("assistant", result)

        logger.info(f"✅ Task completed in {end_time - start_time:.2f} seconds.")
        print(f"\n🤖 Agent Response:\n{result}")

    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        logger.error(traceback.format_exc())
        memory.push("error", f"Error processing prompt: {e}")


async def check_and_process_todo(
    args, llm, config: Config, memory: Memory, parmanus_available: bool
):
    """Check if todo.md exists with a goal and automatically start the agent."""
    todo_path = os.path.join(config.workspace_root, "todo.md")

    if not os.path.exists(todo_path):
        return False

    try:
        with open(todo_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract goal from todo.md - try different formats
        goal_match = re.search(r"\*\*Goal:\*\*\s*(.+)", content)
        if goal_match:
            goal = goal_match.group(1).strip()
        else:
            # Try simpler format - look for content after "# Task Todo List"
            lines = content.strip().split("\n")
            goal = None
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("**"):
                    goal = line
                    break

        if not goal or len(goal) < 3:
            return False

        logger.info(f"📋 Found todo.md with goal: {goal}")
        logger.info("🤖 Auto-starting agent to work on todo.md...")

        # Create prompt to work on the todo
        auto_prompt = f"Work on the todo.md file. The goal is: {goal}. Please read the todo.md, create a detailed action plan with specific steps, and execute the tasks autonomously."

        await process_prompt(auto_prompt, args, llm, config, memory, parmanus_available)
        return True

    except Exception as e:
        logger.error(f"Error reading todo.md: {e}")

    return False
