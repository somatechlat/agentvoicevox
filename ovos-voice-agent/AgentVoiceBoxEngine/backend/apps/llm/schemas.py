"""
Pydantic Schemas for LLM Configuration and Testing
=================================================

This module defines the Pydantic schemas used for validating and serializing
data related to Large Language Model (LLM) configurations and testing.
These schemas are crucial for securely handling LLM provider credentials
and for structuring requests and responses for LLM interactions.
"""

from typing import Optional

from ninja import Schema


class LLMConfigOut(Schema):
    """
    Defines the response structure for an LLM configuration.

    This schema includes placeholders for sensitive API keys, which are typically
    retrieved from a secure vault.
    """

    provider: str  # The name of the LLM provider (e.g., 'openai', 'groq', 'ollama').
    model: str  # The specific LLM model being used (e.g., 'gpt-4', 'llama-3.3-70b-versatile').
    temperature: float  # The LLM's creativity/randomness setting (0.0 to 2.0).
    max_tokens: int  # The maximum number of tokens for an LLM response.
    openai_api_key: str = ""  # Placeholder for OpenAI API key (retrieved from Vault).
    groq_api_key: str = ""  # Placeholder for Groq API key (retrieved from Vault).
    ollama_base_url: str = ""  # Placeholder for Ollama base URL (retrieved from Vault).


class LLMConfigUpdate(Schema):
    """
    Defines the request payload for updating an LLM configuration.
    All fields are optional to allow for partial updates (PATCH).
    Includes fields for sensitive credentials which will be stored in Vault.
    """

    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    openai_api_key: Optional[str] = None  # New OpenAI API key. Set to None to clear.
    groq_api_key: Optional[str] = None  # New Groq API key. Set to None to clear.
    ollama_base_url: Optional[str] = None  # New Ollama base URL. Set to None to clear.


class LLMTestRequest(Schema):
    """
    Defines the request payload for testing an LLM configuration.
    """

    prompt: str  # The text prompt to send to the LLM for testing.


class LLMTestResponse(Schema):
    """
    Defines the response structure for an LLM test.
    """

    response: str  # The text response received from the LLM.
