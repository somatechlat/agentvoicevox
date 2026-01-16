"""
MCP Server Factory
==================
Centralized factory for creating the Model Context Protocol (MCP) server instance.

This module ensures that both the CLI management command (Stdio) and the
API endpoints (SSE) use the exact same server configuration and tool registry,
maintaining consistency across different transport mechanisms.
"""

import logging

from mcp.server.fastmcp import FastMCP
from apps.mcp.tools import list_voices, generate_speech

logger = logging.getLogger(__name__)

def create_mcp_server() -> FastMCP:
    """
    Factory function to create the AgentVoiceBox MCP Server instance.
    This ensures consistency between Stdio and SSE transports.
    """
    mcp = FastMCP("AgentVoiceBox")

    # Register Tools
    mcp.tool()(list_voices)
    mcp.tool()(generate_speech)

    @mcp.tool()
    def get_server_status() -> str:
        """Returns the status of the AgentVoiceBox platform."""
        return "AgentVoiceBox Platform is ONLINE"

    @mcp.tool()
    def list_capabilities() -> list[str]:
        """Lists available platform capabilities."""
        return ["voice_synthesis", "voice_cloning", "billing", "tenant_management"]

    return mcp
