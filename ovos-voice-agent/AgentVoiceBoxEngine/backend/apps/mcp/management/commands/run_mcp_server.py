"""
MCP Server Management Command
=============================
Django management command to run the MCP Server via Stdio or SSE.

This command serves as the primary entry point for:
1. Local Agents: Running via `transport="stdio"` (default) for direct integration with IDEs (Cursor/Windsurf) or local LLMs.
2. Debugging: Validating tool registration and server startup.

Usage:
    python manage.py run_mcp_server --transport stdio
    python manage.py run_mcp_server --transport sse  # (Typically handled via ASGI, but available for testing)
"""

import logging
from typing import Any, Optional

from django.core.management.base import BaseCommand
from apps.mcp.server_factory import create_mcp_server

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command to run the MCP server.
    
    This command initializes and runs the MCP server, handling
    requests from external MCP clients. It supports command-line
    configuration of server parameters.
    """
    
    help = "Starts the MCP (Model Context Protocol) server"
    
    def add_arguments(self, parser):
        """
        Adds command-line arguments for the MCP server.
        
        Args:
            parser: Argument parser for the management command
        """
        parser.add_argument(
            "--transport",
            type=str,
            default="stdio",
            choices=["stdio", "sse"],
            help="Transport mechanism to use (default: stdio)",
        )
    
    def handle(self, *args, **options):
        """
        Handles the MCP server startup logic.
        """
        transport = options["transport"]
        
        self.stdout.write(f"Starting AgentVoiceBox MCP Server via {transport}...")

        # Initialize the MCP Server using the shared factory
        mcp = create_mcp_server()

        # Run the server
        if transport == "stdio":
            # FastMCP.run() handles the event loop
            try:
                mcp.run(transport="stdio")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Server crashed: {e}"))
                raise
        elif transport == "sse":
             self.stdout.write(self.style.WARNING("SSE Mode via CLI is for testing only. Use the ASGI application for production."))
             # In a real scenario, we might start a uvicorn server here, but for now we just verify instantiation
             self.stdout.write(self.style.SUCCESS("MCP Server instance created successfully."))
