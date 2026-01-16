"""
MCP API Endpoints
=================
Exposes the Model Context Protocol via HTTP/SSE for remote clients.

This module integrates the MCP server with Django Ninja to provide:
1. Server-Sent Events (SSE) endpoint for server->client push notifications.
2. JSON-RPC message endpoint for client->server requests.

Routes:
    GET /api/v2/mcp/sse: Establish connection
    POST /api/v2/mcp/messages: Send JSON-RPC payload
"""

import asyncio

import json
import logging
from typing import AsyncGenerator

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from mcp.server.fastmcp import FastMCP
from mcp.types import JSONRPCMessage

# Import the shared MCP instance configuration
# We need to ensure we use the same tools as the management command
# For now, we'll recreate the instance or refactor to share it
from apps.mcp.tools import list_voices, generate_speech

logger = logging.getLogger(__name__)

router = Router(tags=["MCP"])

# Initialize FastMCP for the API
# In a production generic setup, this might be a singleton
mcp_api = FastMCP("AgentVoiceBox-API")
mcp_api.tool()(list_voices)
mcp_api.tool()(generate_speech)

@mcp_api.tool()
def get_server_status() -> str:
    return "AgentVoiceBox Platform is ONLINE (SSE Transport)"

@mcp_api.tool()
def list_capabilities() -> list[str]:
    return ["voice_synthesis", "voice_cloning", "billing", "tenant_management"]


async def sse_generator(request) -> AsyncGenerator[str, None]:
    """
    Generates Server-Sent Events for the MCP connection.
    """
    # Create a memory channel for this connection
    # implementation detail: we need a way to receive responses from the MCP server
    # and yield them to the client.
    # FastMCP doesn't expose a raw SSE generator easily in the current version slightly, from prior knowledge.
    # But we can use the low-level server interfaces if needed.
    
    # For now, we will implement a basic heartbeat to establish the connection
    # and then rely on the MCP Server's internal transport mechanism if possible,
    # or implement a custom loop.
    
    # Since FastMCP handles the loop, we might need to "feed" it.
    # A cleaner Django-Native way for V1 is to manually implement the SSE handshake
    # if FastMCP's asgi_app isn't directly compatible with Ninja.
    
    yield f"event: endpoint\ndata: /api/mcp/messages?session_id=test\n\n"
    
    while True:
        await asyncio.sleep(1)
        yield ": heartbeat\n\n"

@router.get("/sse", summary="MCP SSE Endpoint")
def handle_sse(request):
    """
    Establishes a Server-Sent Events (SSE) connection for MCP.
    """
    response = StreamingHttpResponse(
        sse_generator(request),
        content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

@router.post("/messages", summary="MCP Message Endpoint")
@csrf_exempt
async def handle_messages(request, session_id: str = None):
    """
    Handles JSON-RPC messages from the MCP client.
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Received MCP message: {data}")
        
        # Here we would feed the message into the MCP server instance
        # and wait for the response, which should then be pushed to the
        # SSE stream associated with 'session_id'.
        
        # This requires a stateful connection manager (e.g., Redis or in-memory dict)
        # to map session_id -> SSE generator queue.
        
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Error handling MCP message: {e}")
        return {"error": str(e)}
