"""
Function calling engine for realtime sessions.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class FunctionCallingEngine:
    """Manage function registration, validation, and execution."""

    def __init__(self) -> None:
        """Initializes the FunctionCallingEngine, setting up an empty function registry."""
        self._functions: dict[str, dict[str, Any]] = {}

    def register_function(self, name: str, schema: dict, handler: Callable) -> None:
        """Register a function with schema and handler."""
        self._functions[name] = {"schema": schema, "handler": handler}
        logger.info("Registered function", extra={"name": name})

    async def execute_function(self, function_name: str, arguments: dict) -> dict[str, Any]:
        """Execute a registered function."""
        function = self._functions.get(function_name)
        if not function:
            return {"success": False, "error": "Function not found"}

        handler = function["handler"]
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)
            return {"success": True, "result": result}
        except Exception as exc:
            logger.exception("Function execution error", extra={"name": function_name})
            return {"success": False, "error": str(exc)}

    def validate_arguments(self, function_name: str, arguments: dict) -> tuple[bool, Optional[str]]:
        """Validate arguments against the registered schema."""
        function = self._functions.get(function_name)
        if not function:
            return False, "Function not found"

        schema = function["schema"]
        parameters = schema.get("parameters", {})
        required = parameters.get("required", [])
        properties = parameters.get("properties", {})

        for param in required:
            if param not in arguments:
                return False, f"Missing required parameter: {param}"

        for param in arguments:
            if param not in properties:
                return False, f"Unknown parameter: {param}"

        return True, None


_engine = FunctionCallingEngine()


def get_function_engine() -> FunctionCallingEngine:
    """Return the singleton function engine."""
    return _engine
