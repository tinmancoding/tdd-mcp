# TDD-MCP Server

A Model Context Protocol (MCP) server that enforces disciplined Test-Driven Development workflows by managing session state and providing guided phase transitions. It ensures developers and AI agents follow proper TDD methodology through explicit state management and evidence-based phase transitions.

## Overview

The TDD-MCP Server helps maintain TDD discipline by:

- **Enforcing strict TDD cycle**: Write failing test → Implement → Refactor → Repeat
- **Maintaining session state persistence** across restarts
- **Providing clear guidance** to agents without requiring special system prompts
- **Supporting session pause/resume** functionality
- **Enabling custom rule extensions** per session

## Features

### Session Management
- Start new TDD sessions with specific goals and file configurations
- Pause and resume sessions across server restarts
- Update session parameters as projects evolve
- Complete audit trail through event sourcing

### Workflow Control
- Guided phase transitions with evidence requirements
- Rollback capability to previous phases
- Real-time state tracking and suggestions
- Built-in TDD rule enforcement

### Agent Integration
- Zero-configuration setup for AI agents
- Context-aware guidance and prompts
- Natural language command shortcuts
- Rich session history and logging

## Quick Start

### Installation

```bash
# Install with uv (recommended)
uv add tdd-mcp

# Or with pip
pip install tdd-mcp
```

### Starting the Server

```bash
# Using the CLI command
tdd-mcp

# Or with uv
uv run tdd-mcp

# Or directly with Python
python -m tdd_mcp.main

# For development (runs from source)
uv run python -m tdd_mcp.main
```

### Basic Usage

Once the server is running, agents can interact with these MCP tools:

```python
# Start a new session
start_session(
    goal="Implement user authentication system",
    test_files=["tests/test_auth.py"],
    implementation_files=["src/auth.py"],
    run_tests=["pytest tests/test_auth.py -v"]
)

# Check current state and get guidance
get_current_state()

# Move to next phase with evidence
next_phase("wrote failing test for login validation")

# Add contextual logs
log("considering edge case for empty passwords")

# View session history
history()
```

## TDD Workflow

The server enforces a strict 3-phase TDD cycle:

1. **📝 WRITE_TEST**: Write ONE failing test
2. **✅ IMPLEMENT**: Write minimal code to make the test pass  
3. **🔧 REFACTOR**: Improve code/tests (optional, can be skipped)

Each phase transition requires evidence of what was accomplished, ensuring thoughtful progression through the TDD cycle.

## Testing with AI Editors

The TDD-MCP server communicates using the Model Context Protocol (MCP) over stdin/stdout. AI editors automatically start and manage the server process when properly configured.

### VS Code with Copilot Chat

VS Code has native MCP support. Configure the server in your workspace or user settings:

1. **Create MCP configuration** in `.vscode/mcp.json` (workspace) or your user profile:
   ```json
   {
     "servers": {
       "tdd-mcp": {
         "type": "stdio",
         "command": "uv",
         "args": ["run", "python", "-m", "tdd_mcp.main"],
         "cwd": "${workspaceFolder}/path/to/tdd-mcp"
       }
     }
   }
   ```

2. **Test the server** by using `@` in Copilot Chat and selecting MCP tools

### VS Code with Continue Extension

Configure Continue to use the TDD-MCP server:

1. **Add to Continue config** (`config.json`):
   ```json
   {
     "experimental": {
       "modelContextProtocolServer": {
         "transport": {
           "type": "stdio",
           "command": "uv",
           "args": ["run", "python", "-m", "tdd_mcp.main"],
           "cwd": "/path/to/tdd-mcp"
         }
       }
     }
   }
   ```

2. **Use MCP context** by typing `@` and selecting "MCP" from the dropdown

### Cursor

Use the FastMCP CLI for easy installation:

```bash
# Install with FastMCP CLI (recommended)
cd /path/to/tdd-mcp
fastmcp install cursor src/tdd_mcp/main.py

# Or manually configure in ~/.cursor/mcp.json
```

Manual configuration:
```json
{
  "mcpServers": {
    "tdd-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "tdd_mcp.main"],
      "cwd": "/path/to/tdd-mcp"
    }
  }
}
```

### Claude Code (CLI)

Use the FastMCP CLI or manual configuration:

```bash
# With FastMCP CLI
cd /path/to/tdd-mcp
fastmcp install claude-code src/tdd_mcp/main.py

# Or manual installation
claude mcp add tdd-mcp -- uv run --with fastmcp fastmcp run src/tdd_mcp/main.py
```

### Claude Desktop

Configure in the Claude Desktop config file:

```bash
# With FastMCP CLI
cd /path/to/tdd-mcp
fastmcp install claude-desktop src/tdd_mcp/main.py
```

Manual configuration location varies by OS:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Local Development Testing

For development and debugging:

```bash
# Start the server manually to see logs
cd /path/to/tdd-mcp
uv run python -m tdd_mcp.main

# Enable debug logging
TDD_MCP_LOG_LEVEL=debug uv run python -m tdd_mcp.main
```

### Package Installation Method

For production use, install as a package:

```bash
# Install from PyPI (when published)
pip install tdd-mcp

# Or install locally in development mode
cd /path/to/tdd-mcp
uv pip install -e .
```

Then use the simpler configuration:
```json
{
  "command": "tdd-mcp",
  "args": []
}

### Testing the MCP Tools

Once connected, you can test these core workflows:

1. **Initialize and explore**:
   ```
   Ask your AI: "Call the initialize() tool to learn about TDD-MCP"
   ```

2. **Start a session**:
   ```
   Ask your AI: "Start a TDD session for implementing a calculator with tests in tests/test_calc.py and implementation in src/calc.py"
   ```

3. **Check status**:
   ```
   Ask your AI: "What's the current TDD state?"
   ```

4. **Follow the workflow**:
   ```
   Ask your AI: "Help me write a failing test for addition"
   # Then: "Move to the next phase after writing the test"
   # Then: "Implement the minimal code to make the test pass"
   ```

### Debugging Connection Issues

If you encounter connection issues:

1. **Check MCP configuration** - ensure the command and args are correct
2. **Verify working directory** - the `cwd` should point to the tdd-mcp project
3. **Test manual startup** to see error messages:
   ```bash
   cd /path/to/tdd-mcp
   uv run python -m tdd_mcp.main
   ```
4. **Enable verbose logging** by setting environment variable:
   ```bash
   TDD_MCP_LOG_LEVEL=debug uv run python -m tdd_mcp.main
   ```
5. **Check editor logs** - most editors have MCP debugging logs available

### Example Session Flow

A typical testing session might look like:

```
User: "Initialize TDD-MCP and start a session for a string utility library"
AI: [Calls initialize() and start_session()]

User: "What should I do next?"
AI: [Calls get_current_state() and provides guidance]

User: "I wrote a failing test for string reversal"
AI: [Calls next_phase() with evidence]

User: "Show me the session history"
AI: [Calls history() and displays the timeline]
```

## Architecture

### Event Sourcing
- **Complete Audit Trail**: Every action, phase change, and log entry preserved
- **Rollback Capability**: Navigate backward through phases when needed
- **State Consistency**: Current state calculated from authoritative event stream
- **Future-Proof**: New event types can be added without breaking existing sessions

### Repository Pattern
- **Pluggable Storage**: Abstract repository interface with filesystem implementation
- **Concurrency Safety**: Lock file mechanism prevents concurrent session access
- **Session Persistence**: JSON event streams survive server restarts

### MCP Integration
- **FastMCP V2**: Built on the latest MCP framework
- **Rich Tool Set**: 12 comprehensive tools for session and workflow management
- **Error Handling**: Structured error responses with recovery suggestions

## Configuration

### Environment Variables

- **`TDD_MCP_SESSION_DIR`**: Custom session storage directory (default: `.tdd-mcp/sessions/`)
- **`TDD_MCP_LOG_LEVEL`**: Logging verbosity - `debug|info|warn|error` (default: `info`)

### Session Structure

Sessions are stored as JSON event streams:

```json
{
  "schema_version": "1.0",
  "events": [
    {
      "timestamp": "2025-07-11T10:30:00Z",
      "event_type": "session_started",
      "data": {
        "goal": "Implement user authentication",
        "test_files": ["tests/test_auth.py"],
        "implementation_files": ["src/auth.py"],
        "run_tests": ["pytest tests/test_auth.py -v"]
      }
    }
  ]
}
```

## Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management

### Setup

```bash
# Clone the repository
git clone https://github.com/tinmancoding/tdd-mcp.git
cd tdd-mcp

# Install dependencies
uv sync

# Install development dependencies
uv sync --group dev
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=tdd_mcp

# Run specific test file
uv run pytest tests/domain/test_session.py

# Run tests in watch mode
uv run pytest-watch
```

### Development Workflow

The project itself follows TDD principles:

1. **Write failing tests first** for new functionality
2. **Implement minimal code** to make tests pass
3. **Refactor** for code quality while keeping tests green

### Project Structure

```
src/tdd_mcp/
├── main.py                    # FastMCP server entry point
├── handlers/                  # MCP tool handlers
│   ├── session_handlers.py    # start_session, update_session, etc.
│   ├── workflow_handlers.py   # next_phase, rollback, get_current_state
│   ├── logging_handlers.py    # log, history
│   └── guidance_handlers.py   # initialize, quick_help
├── domain/                    # Core business logic
│   ├── session.py            # TDDSession class
│   ├── events.py             # Event schemas and TDDEvent
│   └── exceptions.py         # Custom exception classes
├── repository/                # Data persistence layer
│   ├── base.py               # Abstract TDDSessionRepository
│   └── filesystem.py         # FileSystemRepository implementation
└── utils/                     # Supporting utilities
    ├── config.py             # Environment variable handling
    └── logging.py            # Logging configuration
```

### Building and Publishing

```bash
# Build the package
uv build

# Install locally for testing
uv pip install -e .

# Publish to PyPI (maintainers only)
uv publish
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow TDD: Write tests first, then implement
4. Ensure all tests pass (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/tinmancoding/tdd-mcp/issues)
- **Documentation**: See the [PRD](aidocs/PRD-initial.md) for detailed specifications
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Practice what we preach**: This TDD-MCP server was built using the same TDD discipline it aims to enforce!
