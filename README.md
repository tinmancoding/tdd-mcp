# TDD-MCP Server (Experimental)

A Model Context Protocol (MCP) server that focuses on disciplined Test-Driven Development workflows by managing session state and providing guided phase transitions. It ensures developers and AI agents follow proper TDD methodology through explicit state management and evidence-based phase transitions.

## What This MCP Server Does

**TDD-MCP acts as your TDD coach**, guiding you through proper Test-Driven Development cycles by:

- **🔄 Enforcing the 3-phase TDD cycle**: Write failing test → Implement → Refactor → Repeat
- **🎯 Maintaining focus on one goal at a time** with clear success criteria
- **📝 Tracking your progress** through persistent session state
- **🛡️ Guiding against TDD violations** like implementing before writing tests
- **🧭 Providing contextual guidance** at every step

## ⚠️ Important Considerations

**Token Usage Warning**
This MCP server significantly increases token usage for LLM interactions. Modern LLMs like Claude Sonnet can generate complete classes and test files in a single response, but TDD-MCP deliberately constrains this to enforce disciplined development. Consider the trade-off between development speed and TDD discipline.

**Not Ideal For:**
- Large-scale refactoring or architectural changes
- Simple CRUD operations or boilerplate code
- When you need to generate many files quickly
- Prototyping or exploratory development phases

## Quickstart Guide

Get up and running with TDD-MCP in minutes:

### 1. Configure the MCP Server

Choose your AI editor and add TDD-MCP to your configuration:

**VS Code with Copilot Chat:**
```json
// .vscode/mcp.json
{
  "servers": {
    "tdd-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "tdd_mcp.main"],
      "cwd": "/path/to/tdd-mcp"
    }
  }
}
```

**Cursor:**
```json
// ~/.cursor/mcp.json
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

### 2. Start a New Agent Chat

Open your AI editor and start a new conversation. The TDD-MCP server will automatically connect.

### 3. Initialize TDD-MCP

Teach your AI editor the basics of TDD-MCP by using the built-in initialize prompt:

**In VS Code with Copilot Chat:**
```
@tdd-mcp.initialize
```

**In other editors, paste this:**

Some AI editors may require a different format, but the goal is to trigger the `initialization` prompt. This prompt provides all the instructions on how to use TDD-MCP effectively in the Model's context.


### 4. Plan Your Session

Start planning with the session wizard:

```
I want to implement a password validator function. 
Please use the start_session_wizard prompt to help me set up the session parameters.
```

Or directly ask your AI:

```
Help me start a TDD session for implementing a password validator that checks:
- Minimum 8 characters
- At least one uppercase letter
- At least one number
```

### 5. Start Your TDD Session

Your AI will call `start_session()` with the planned parameters:

```python
start_session(
    goal="Implement password validator with length, uppercase, and number requirements",
    test_files=["tests/test_password_validator.py"],
    implementation_files=["src/password_validator.py"],
    run_tests=["pytest tests/test_password_validator.py -v"]
)
```

### 6. Follow the Red-Green-Refactor Flow

Work with your AI through the TDD cycle:

**🔴 Red Phase (Write Failing Test):**
```
Let's write our first failing test for minimum length validation.
```

**🟢 Green Phase (Make Test Pass):**
```
Now let's implement the minimal code to make this test pass.
```

**🔵 Refactor Phase (Improve Code):**
```
Let's refactor to improve the code quality while keeping tests green.
```

### 7. Add Logs Anytime

Capture your thoughts during development:

```
Log: "Considering if we should validate empty strings separately"
```

```
Log: "Found a good pattern for chaining validation rules"
```

### 8. End the Session

When you've reached your goal:

```
We've successfully implemented the password validator with all requirements. 
Please call end_session() to complete our TDD session.
```

You'll get a summary of what was accomplished during the session.

### 🎉 You're Ready!

You now have:
- ✅ A working TDD workflow with AI guidance
- ✅ Complete session history and audit trail
- ✅ Disciplined test-first development
- ✅ Evidence-based phase transitions

## How It Works

### TDD Phase Management
The server maintains strict control over the TDD workflow:

1. **📝 WRITE_TEST Phase**: You can only modify test files. Write ONE failing test that captures the next small increment of functionality.

2. **✅ IMPLEMENT Phase**: You can only modify implementation files. Write the minimal code needed to make the failing test pass.

3. **🔧 REFACTOR Phase**: You can modify both test and implementation files. Improve code quality without changing behavior.

Each phase transition requires **evidence** - you must describe what you accomplished to justify moving to the next phase.

### State Persistence
- Sessions persist across server restarts
- Complete audit trail of all actions through event sourcing
- Pause/resume functionality for long-running projects
- Session history shows your TDD journey

### File Access Guidance
The server provides guidance on which files to modify based on your current TDD phase:
- **WRITE_TEST**: Only test files specified in your session
- **IMPLEMENT**: Only implementation files specified in your session
- **REFACTOR**: Both test and implementation files

*Note: This is guidance for your AI assistant - the server doesn't enforce file system restrictions.*

## When to Use TDD-MCP?

**🎯 Mission-Critical Features**
- Use when building components where bugs have serious consequences
- Perfect for core business logic, security features, or data integrity functions
- When you need rock-solid reliability and comprehensive test coverage

**📏 Small, Focused Goals**
- Best for goals that fit within a single context window
- Ideal for individual functions, classes, or small modules
- When you can clearly define "done" in a few sentences

**🧠 Learning TDD Discipline**
- Excellent for developers new to Test-Driven Development
- Helps build muscle memory for the Red-Green-Refactor cycle
- Provides structured guidance when working with AI assistants

**� Complex Logic Development**
- When you need to think through edge cases step by step
- For algorithms or business rules that benefit from incremental development
- When you want to document your thought process through tests


## Available MCP Tools & Prompts

When you connect to the TDD-MCP server, you get access to these tools and prompts:

### 🚀 Session Management Tools

#### `start_session(goal, test_files, implementation_files, run_tests, custom_rules)`
Start a new TDD session with:
- **goal**: Clear, testable objective with definition of done
- **test_files**: List of test files you're allowed to modify (e.g., `["tests/test_auth.py"]`)
- **implementation_files**: List of implementation files you're allowed to modify (e.g., `["src/auth.py"]`)
- **run_tests**: Commands to run your tests (e.g., `["pytest tests/test_auth.py -v"]`)
- **custom_rules**: Additional TDD rules specific to your project (optional)

Returns: Session ID string

#### `update_session(...)` 
Update any session parameters as your project evolves. Returns `True` if successful.

#### `pause_session()` / `resume_session(session_id)`
Pause your current session and resume it later (even after server restart). 
- `pause_session()` returns the session ID
- `resume_session(session_id)` returns a `TDDSessionState` object

#### `end_session()`
Complete your session and get a summary of what was accomplished. Returns summary string.

### 🔄 Workflow Control Tools

#### `get_current_state()`
**Use this frequently!** Returns a `TDDSessionState` object with your current TDD phase, cycle number, allowed files, and suggested next actions.

#### `next_phase(evidence_description)`
Move to the next TDD phase by providing evidence of what you accomplished. Returns a `TDDSessionState` object with the new phase:
- From WRITE_TEST → IMPLEMENT: "wrote failing test for user login validation"
- From IMPLEMENT → REFACTOR: "implemented basic login function, test now passes"
- From REFACTOR → WRITE_TEST: "refactored login code for better error handling"

#### `rollback(reason)`
Go back to the previous phase if you made a mistake. Returns a `TDDSessionState` object with the previous phase:
- "realized I implemented too much functionality in one test"
- "need to write a better test first"

### 📝 Logging & History Tools

#### `log(message)`
Add notes to your session without affecting workflow state. Returns `True` if successful:
- "considering edge case for empty passwords"
- "found useful pattern in existing codebase"

#### `history()`
View your complete TDD journey - all phase transitions, logs, and evidence. Returns a list of formatted history strings.

### 🧭 Guidance & Help

#### `initialize` (Prompt)
Get comprehensive instructions for using TDD-MCP effectively. **Use this first** when starting with the server.

#### `start_session_wizard(goal)` (Prompt)
Get personalized guidance for setting up your TDD session. Analyzes your workspace and suggests optimal session parameters.

#### `quick_help()`
Get context-aware help and shortcuts based on your current phase and session state. Returns a dictionary with available actions and reminders.


## How Session Management Works

### State Persistence
Your TDD sessions are automatically saved and persist across server restarts:

**🔄 Event Sourcing**
- Every action you take is recorded as an event
- Your session state is calculated from these events
- Complete audit trail of your TDD journey
- Rollback capability to previous phases

**💾 Automatic Saving**
- Sessions are saved to `.tdd-mcp/sessions/` directory
- Each session gets a unique JSON file
- No manual save/load required
- Safe concurrent access with file locking

**⏸️ Pause & Resume**
- Pause your session anytime with `pause_session()`
- Resume later with `resume_session(session_id)`
- Perfect for long-running projects
- Session state preserved exactly as you left it

### Session Lifecycle

```
📋 PLANNING
├── Use start_session_wizard prompt for guided setup
├── Review suggested parameters
└── Call start_session() to begin (returns session ID)

🔄 ACTIVE TDD CYCLES
├── Phase: WRITE_TEST → write failing test
├── Phase: IMPLEMENT → make test pass  
├── Phase: REFACTOR → improve code quality
└── Repeat cycles until goal achieved

⏸️ PAUSE/RESUME (Optional)
├── Call pause_session() to save state (returns session ID)
├── Server can restart, system can reboot
└── Call resume_session() to continue (returns TDDSessionState)

✅ COMPLETION
├── Call end_session() when goal achieved (returns summary)
└── Get summary of what was accomplished
```

### File Access Guidance

The server provides guidance on which files should be modified based on your current TDD phase:

- **📝 WRITE_TEST Phase**: Only your specified test files should be modified
- **✅ IMPLEMENT Phase**: Only your specified implementation files should be modified  
- **🔧 REFACTOR Phase**: Both test and implementation files can be modified

*Note: This is guidance provided to your AI assistant through the MCP tools - the server doesn't enforce file system restrictions. Your AI can still choose to modify any files, but the server helps it understand which files are appropriate for each TDD phase.*


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
- **`TDD_MCP_USE_MEMORY_REPOSITORY`**: Use in-memory storage for testing (default: `false`)

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
