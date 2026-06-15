from typing import Any


def route_agent(prompt: str, use_full_agents: bool = True) -> str:
    """Intelligently route to appropriate agent based on prompt analysis."""
    prompt_lower = prompt.lower()

    # Simple Python execution tasks - route to code agent for direct execution
    if any(
        phrase in prompt_lower
        for phrase in [
            "print hello",
            "print 'hello",
            'print "hello',
            "execute python",
            "run python",
            "python print",
        ]
    ) and not any(
        word in prompt_lower
        for word in [
            "complex",
            "research",
            "analyze",
            "plan",
            "todo",
            "file",
            "save",
            "create file",
        ]
    ):
        return "code"

    # Simple code-only tasks (no research, no complex reasoning needed)
    if any(
        word in prompt_lower
        for word in ["debug this code", "fix this function", "compile", "syntax error"]
    ) and not any(
        word in prompt_lower
        for word in [
            "research",
            "find",
            "search",
            "latest",
            "news",
            "current",
            "today",
            "recent",
        ]
    ):
        return "code"

    # Simple file operations (basic read/write without research or complex processing)
    if any(
        phrase in prompt_lower
        for phrase in ["just read file", "only save this", "simple file copy"]
    ) and not any(
        word in prompt_lower
        for word in [
            "analyze",
            "research",
            "find",
            "search",
            "create",
            "generate",
            "write content",
        ]
    ):
        return "file"

    # For everything else, use the intelligent manus agent which can:
    # - Browse the web for real information
    # - Create proper todo and markdown files
    # - Use reasoning and planning
    # - Handle complex multi-step tasks
    # - Coordinate multiple capabilities

    # Specifically route these to manus for intelligent handling:
    if any(
        phrase in prompt_lower
        for phrase in [
            "write",
            "create",
            "generate",
            "make",
            "build",
            "develop",
            "news",
            "current",
            "today",
            "latest",
            "recent",
            "update",
            "research",
            "find",
            "search",
            "analyze",
            "review",
            "investigate",
            "plan",
            "organize",
            "schedule",
            "task",
            "steps",
            "browse",
            "web",
            "website",
            "url",
            "online",
            "internet",
            "top 10",
            "list of",
            "summary",
            "report",
            "document",
            "accident",
            "crash",
            "collision",
            "safety",
            "risk",
            "prevention",
        ]
    ):
        return "manus"

    # Default to manus for any complex or ambiguous requests
    return "manus"
