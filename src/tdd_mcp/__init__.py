"""TDD-MCP Server - A Model Context Protocol server that enforces Test-Driven Development workflows."""

__version__ = "0.0.1"

def main() -> None:
    """Entry point for the TDD-MCP server."""
    from .main import start_server
    start_server()
