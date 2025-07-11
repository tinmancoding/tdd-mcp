"""Main entry point for TDD-MCP server."""

from fastmcp import FastMCP


def start_server():
    """Start the TDD-MCP server."""
    mcp = FastMCP("TDD-MCP Server")
    
    @mcp.tool
    def hello() -> str:
        """Test tool for basic functionality."""
        return "Hello from TDD-MCP server!"
    
    mcp.run()


if __name__ == "__main__":
    start_server()