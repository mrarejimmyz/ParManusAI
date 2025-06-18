import multiprocessing
import sys
from io import StringIO
from typing import Dict

from app.tool.core.base import BaseTool, ToolConfig, ToolResult


class PythonExecute(BaseTool):
    """A tool for executing Python code with timeout and safety restrictions."""

    def __init__(self, **kwargs):
        # Set up unified configuration
        if "config" not in kwargs:
            kwargs["config"] = ToolConfig(
                name="python_execute",
                description="Executes Python code string. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results.",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Python code to execute.",
                        },
                    },
                    "required": ["code"],
                },
                timeout=30.0,
                retries=1,
                cache_enabled=False,  # Don't cache code execution
            )
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        """Get tool name for compatibility."""
        return self.config.name

    def _run_code(self, code: str, result_dict: dict, safe_globals: dict) -> None:
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            exec(code, safe_globals, safe_globals)
            result_dict["observation"] = output_buffer.getvalue()
            result_dict["success"] = True
        except Exception as e:
            result_dict["observation"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout

    async def _execute(self, **kwargs) -> ToolResult:
        """Execute Python code with unified interface."""
        code = kwargs.get("code", "")
        timeout = kwargs.get("timeout", 5)

        if not code.strip():
            return ToolResult(success=False, error="No code provided to execute")

        try:
            with multiprocessing.Manager() as manager:
                result = manager.dict({"observation": "", "success": False})
                if isinstance(__builtins__, dict):
                    safe_globals = {"__builtins__": __builtins__}
                else:
                    safe_globals = {"__builtins__": __builtins__.__dict__.copy()}

                proc = multiprocessing.Process(
                    target=self._run_code, args=(code, result, safe_globals)
                )
                proc.start()
                proc.join(timeout)

                # Handle timeout
                if proc.is_alive():
                    proc.terminate()
                    proc.join(1)
                    return ToolResult(
                        success=False,
                        error=f"Execution timeout after {timeout} seconds",
                    )

                # Return result
                if result["success"]:
                    return ToolResult(
                        success=True,
                        content=result["observation"]
                        or "Code executed successfully (no output)",
                    )
                else:
                    return ToolResult(success=False, error=result["observation"])

        except Exception as e:
            return ToolResult(
                success=False, error=f"Error executing Python code: {str(e)}"
            )

    # Legacy compatibility method
    async def execute(self, code: str, timeout: int = 5) -> Dict:
        """Legacy interface for backward compatibility."""
        result = await self._execute(code=code, timeout=timeout)

        if result.success:
            return {"observation": result.content, "success": True}
        else:
            return {"observation": result.error, "success": False}
