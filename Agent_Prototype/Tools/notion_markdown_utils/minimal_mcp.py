#!/usr/bin/env python3
"""Minimal MCP server for testing installation."""

from mcp.server.fastmcp import FastMCP, Context

# Create a minimal MCP server with explicit dependencies
mcp = FastMCP(
    "Minimal Test",
    description="Minimal test server",
    dependencies=[]  # No extra dependencies needed
)

@mcp.tool()
def hello(name: str, ctx: Context = None) -> str:
    """Say hello to someone.
    
    Args:
        name: The person to greet
        
    Returns:
        A greeting message
    """
    if ctx:
        ctx.info(f"Greeting {name}")
    return f"Hello, {name}!"

@mcp.resource("test://info")
def get_info() -> str:
    """Get test information."""
    return "This is a minimal test MCP."

if __name__ == "__main__":
    mcp.run()