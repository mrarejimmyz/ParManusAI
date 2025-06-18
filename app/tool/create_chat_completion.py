from typing import Any, List, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel, Field

from app.tool.core import BaseTool, ToolConfig, ToolResult


class CreateChatCompletion(BaseTool):
    """Tool for creating structured completions with specified output formatting."""

    # Type mapping for JSON schema
    type_mapping: dict = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        dict: "object",
        list: "array",
    }
    response_type: Optional[Type] = Field(
        default=str, description="Expected response type"
    )
    required: List[str] = Field(default_factory=lambda: ["response"])

    @property
    def name(self) -> str:
        """Get tool name for compatibility."""
        return self.config.name if hasattr(self, "config") else "create_chat_completion"

    def __init__(self, response_type: Optional[Type] = str, **kwargs):
        """Initialize with a specific response type."""
        # Build the ToolConfig
        config = ToolConfig(
            name="create_chat_completion",
            description="Creates a structured completion with specified output formatting.",
            parameters=self._build_parameters_for_type(response_type),
            llm_enabled=False,  # This tool is for structuring responses, not calling LLM
            cache_enabled=False,
        )

        if "config" not in kwargs:
            kwargs["config"] = config

        super().__init__(**kwargs)
        self.response_type = response_type

    def _build_parameters_for_type(self, response_type: Optional[Type] = None) -> dict:
        """Build parameters schema based on response type."""
        if response_type == str:
            return {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": "The response text that should be delivered to the user.",
                    },
                },
                "required": ["response"],
            }

        if isinstance(response_type, type) and issubclass(response_type, BaseModel):
            schema = response_type.model_json_schema()
            return {
                "type": "object",
                "properties": schema["properties"],
                "required": schema.get("required", ["response"]),
            }

        return self._create_type_schema(response_type)

    def _create_type_schema(self, type_hint: Type) -> dict:
        """Create a JSON schema for the given type."""
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        # Handle primitive types
        if origin is None:
            return {
                "type": "object",
                "properties": {
                    "response": {
                        "type": self.type_mapping.get(type_hint, "string"),
                        "description": f"Response of type {type_hint.__name__}",
                    }
                },
                "required": ["response"],
            }

        # Handle List type
        if origin is list:
            item_type = args[0] if args else Any
            return {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "array",
                        "items": self._get_type_info(item_type),
                    }
                },
                "required": ["response"],
            }

        # Handle Dict type
        if origin is dict:
            value_type = args[1] if len(args) > 1 else Any
            return {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "object",
                        "additionalProperties": self._get_type_info(value_type),
                    }
                },
                "required": ["response"],
            }

        # Handle Union type
        if origin is Union:
            return self._create_union_schema(args)

        # Fallback
        return {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "Response content",
                }
            },
            "required": ["response"],
        }

    def _get_type_info(self, type_hint: Type) -> dict:
        """Get type information for a single type."""
        if isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
            return type_hint.model_json_schema()

        return {
            "type": self.type_mapping.get(type_hint, "string"),
            "description": f"Value of type {getattr(type_hint, '__name__', 'any')}",
        }

    def _create_union_schema(self, types: tuple) -> dict:
        """Create schema for Union types."""
        return {
            "type": "object",
            "properties": {
                "response": {"anyOf": [self._get_type_info(t) for t in types]}
            },
            "required": ["response"],
        }

    async def _execute(self, **kwargs) -> Any:
        """
        Core execution logic - required by BaseTool.
        Delegates to the existing execute method.
        """
        from app.tool.core.base import ToolResult

        try:
            result = await self.execute(**kwargs)
            return ToolResult(success=True, content=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def execute(self, required: list | None = None, **kwargs) -> Any:
        """Execute the chat completion with type conversion.

        Args:
            required: List of required field names or None
            **kwargs: Response data

        Returns:
            Converted response based on response_type
        """
        required = required or self.required

        # Handle case when required is a list
        if isinstance(required, list) and len(required) > 0:
            if len(required) == 1:
                required_field = required[0]
                result = kwargs.get(required_field, "")
            else:
                # Return multiple fields as a dictionary
                return {field: kwargs.get(field, "") for field in required}
        else:
            required_field = "response"
            result = kwargs.get(required_field, "")

        # Type conversion logic
        if self.response_type == str:
            return result

        if isinstance(self.response_type, type) and issubclass(
            self.response_type, BaseModel
        ):
            return self.response_type(**kwargs)

        if get_origin(self.response_type) in (list, dict):
            return result  # Assuming result is already in correct format

        try:
            return self.response_type(result)
        except (ValueError, TypeError):
            return result
