from app.tool.core import BaseTool, ToolConfig, ToolResult


class AskHuman(BaseTool):
    """Add a tool to ask human for help."""

    def __init__(self, **kwargs):
        """Initialize with proper ToolConfig."""
        config = ToolConfig(
            name="ask_human",
            description="Use this tool to ask human for help.",
            parameters={
                "type": "object",
                "properties": {
                    "inquire": {
                        "type": "string",
                        "description": "The question you want to ask human.",
                    }
                },
                "required": ["inquire"],
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
        inquire = kwargs.get("inquire", "")
        try:
            response = input(f"""Bot: {inquire}\n\nYou: """).strip()
            return ToolResult(success=True, content=response)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def execute(self, inquire: str) -> str:
        """Legacy execute method for backward compatibility."""
        return input(f"""Bot: {inquire}\n\nYou: """).strip()
