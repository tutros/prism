"""API client configuration and initialization."""

import os
import ssl
import truststore
import httpx
from functools import lru_cache

from anthropic import AsyncAnthropic
from tavily import AsyncTavilyClient

# Inject Windows certificate store into ssl so httpx picks it up
truststore.inject_into_ssl()


@lru_cache()
def get_anthropic_client() -> AsyncAnthropic:
    """Get or create cached Anthropic client."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return AsyncAnthropic(api_key=api_key)


@lru_cache()
def get_tavily_client() -> AsyncTavilyClient:
    """Get or create cached Tavily client."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")
    return AsyncTavilyClient(api_key=api_key)
