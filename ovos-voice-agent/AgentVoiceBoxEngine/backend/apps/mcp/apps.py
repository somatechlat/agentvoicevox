"""
MCP (Model Context Protocol) Configuration
==========================================
Defines the MCPConfig class for managing MCP integration settings.

This module provides configuration management for the Model Context Protocol
integration, allowing external MCP clients to connect and interact with
the AgentVoiceBox platform.
"""

from django.apps import AppConfig


class MCPConfig(AppConfig):
    """
    Manages Model Context Protocol (MCP) integration settings.
    
    Provides configuration for MCP endpoints and authentication,
    enabling seamless integration with external MCP clients.
    
    Attributes:
        name: The app name
        verbose_name: Human-readable app name
    """
    
    name = "apps.mcp"
    verbose_name = "Model Context Protocol Integration"
    
    def ready(self):
        """
        App initialization hook.
        
        Performs any necessary setup when the app is loaded by Django.
        """
        pass
