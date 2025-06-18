from app.tool.core import BaseTool, ToolConfig, ToolResult

_TERMINATE_DESCRIPTION = """Terminate the interaction when the request is met OR if the assistant cannot proceed further with the task.
When you have finished all the tasks, call this tool to end the work."""


class Terminate(BaseTool):
    """Tool to terminate the interaction when tasks are complete."""

    def __init__(self, **kwargs):
        """Initialize with proper ToolConfig."""
        config = ToolConfig(
            name="terminate",
            description=_TERMINATE_DESCRIPTION,
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "The finish status of the interaction.",
                        "enum": ["success", "failure"],
                    }
                },
                "required": ["status"],
            },
            llm_enabled=False,
            cache_enabled=False,
        )

        if "config" not in kwargs:
            kwargs["config"] = config

        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        """Get tool name for compatibility."""
        return self.config.name

    async def _execute(self, **kwargs) -> ToolResult:
        """
        Core execution logic - required by BaseTool.
        """
        status = kwargs.get("status", "success")
        try:
            message = f"The interaction has been completed with status: {status}"
            return ToolResult(success=True, content=message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def execute(self, status: str) -> str:
        """Legacy execute method for backward compatibility."""
        return f"The interaction has been completed with status: {status}"
