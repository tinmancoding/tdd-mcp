# TDD-MCP Server - Product Requirements Document (v0.1)

## Overview
The TDD-MCP Server is a Model Control Protocol (MCP) server that enforces disciplined Test-Driven Development workflows by managing session state and providing guided phase transitions. It ensures developers and AI agents follow proper TDD methodology through explicit state management and evidence-based phase transitions.

## Core Objectives
- Enforce strict TDD cycle: Write failing test → Implement → Refactor → Repeat
- Maintain session state persistence across restarts
- Provide clear guidance to agents without requiring special system prompts
- Support session pause/resume functionality
- Enable custom rule extensions per session

## Technical Requirements
- **Runtime**: Python 3.12+
- **Framework**: FastMCP V2 for MCP server implementation
- **Dependency Management**: `uv tool` for virtualenv and packaging
- **Persistence**: JSON files for session state storage
- **Compatibility**: Support all MCP-compatible AI agents/editors
- **Package Distribution**: PyPI package for easy installation
- **Core Dependencies**: FastMCP V2, Pydantic (for event validation)
- **Validation**: Pydantic BaseModel for all event data structures with validation rules

## MCP Tools Interface

### Session Management
```python
start_session(
    goal: str,                      # High-level session objective and definition of done
    test_files: List[str],          # Files where agent can write tests (explicit paths)
    implementation_files: List[str], # Files where agent can write implementation
    run_tests: List[str],           # Commands/instructions for running test suite
    custom_rules: List[str]         # Additional rules appended to global TDD rules
) -> str                            # Returns session_id

update_session(
    goal?: str,                     # All parameters optional for updates
    test_files?: List[str],
    implementation_files?: List[str], 
    run_tests?: List[str],
    custom_rules?: List[str]
) -> bool                           # Returns success status

resume_session(session_id: str) -> TDDSessionState
pause_session() -> str              # Returns session_id
end_session() -> str                # Returns summary
```

### Workflow Control
```python
next_phase(evidence_description: str) -> TDDSessionState
rollback(reason: str) -> TDDSessionState
get_current_state() -> TDDSessionState
```

### Logging & History
```python
log(message: str) -> bool               # Returns success status
history() -> List[str]                  # Returns formatted history entries
```

### Agent Guidance & Prompts
```python
initialize() -> str                     # MCP Prompt - comprehensive TDD-MCP usage instructions
start_session_wizard(goal: str) -> str  # MCP Prompt - guided session setup
quick_help() -> Dict[str, Any]          # Returns command shortcuts and context
```

## Workflow State Machine

### Phases
1. **write_test**: Agent writes ONE failing test
2. **implement**: Agent writes minimal code to make test pass
3. **refactor**: Agent improves code/tests (can be skipped)

### State Transitions
- New sessions always start in `write_test` phase
- Resume can start in any phase based on saved state  
- Normal flow: `write_test` → `implement` → `refactor` → `write_test`
- Refactor can be skipped: `write_test` → `implement` → `write_test`
- `rollback()` moves to previous phase (one step back, including cross-cycle transitions)
- Phase transitions hard-coded in TDDSession class logic

### State Information
```json
{
    "session_id": "uuid",
    "current_phase": "write_test|implement|refactor",
    "current_task": "Write a failing test for user authentication",
    "cycle_number": 3,
    "goal": "Implement user authentication system",
    "files": {
        "test_files": ["tests/test_auth.py"],
        "implementation_files": ["src/auth.py"],
        "run_tests": ["pytest tests/test_auth.py -v"]
    },
    "allowed_files": ["tests/test_auth.py"],  # Current phase restrictions
    "suggested_next_action": "Write a single failing test...",
    "rules_reminder": ["Follow TDD cycle strictly", "Custom rule 1"],
    "ready_for_next_phase": false
}
```

## Implementation Architecture

### Event Schema Design
```python
# Common event envelope using Pydantic
class TDDEvent(BaseModel):
    timestamp: datetime
    event_type: str
    data: Union[SessionStartedEvent, PhaseChangedEvent, LogEntryEvent, RollbackEvent, ...]

# Individual event schemas with validation
class SessionStartedEvent(BaseModel):
    goal: str = Field(min_length=1)
    test_files: List[str] = Field(min_items=1)
    implementation_files: List[str] = Field(min_items=1)
    run_tests: List[str] = Field(min_items=1)
    custom_rules: List[str] = []

class PhaseChangedEvent(BaseModel):
    from_phase: Optional[str]  # None for initial phase
    to_phase: str = Field(regex="^(write_test|implement|refactor)$")
    evidence: str = Field(min_length=1)
    cycle_number: int = Field(ge=1)

class LogEntryEvent(BaseModel):
    message: str = Field(min_length=1)

class RollbackEvent(BaseModel):
    from_phase: str
    to_phase: str
    reason: str = Field(min_length=1)
```

### Repository Pattern
```python
class TDDSessionRepository(ABC):
    @abstractmethod
    def load_events(self, session_id: str) -> List[TDDEvent]
    
    @abstractmethod
    def append_event(self, session_id: str, event: TDDEvent) -> None
    
    @abstractmethod
    def session_exists(self, session_id: str) -> bool
    
    @abstractmethod
    def create_lock(self, session_id: str, metadata: dict) -> None
    
    @abstractmethod
    def remove_lock(self, session_id: str) -> None
    
    @abstractmethod
    def is_locked(self, session_id: str) -> bool

# File-based implementation
class FileSystemRepository(TDDSessionRepository):
    # Implements all abstract methods using JSON files and lock files

# In-memory implementation for testing
class InMemoryRepository(TDDSessionRepository):
    # Implements all abstract methods using in-memory storage
    # Used when TDD_MCP_USE_MEMORY_REPOSITORY environment variable is set
```

### Session Management
```python
class TDDSessionState:
    session_id: str
    current_phase: str
    cycle_number: int
    goal: str
    test_files: List[str]
    implementation_files: List[str]
    run_tests: List[str]
    custom_rules: List[str]
    
    # Calculated properties (not stored)
    @property
    def allowed_files(self) -> List[str]
    
    @property 
    def suggested_next_action(self) -> str
    
    @property
    def rules_reminder(self) -> List[str]

class TDDSession:
    def __init__(self, session_id: str, repository: TDDSessionRepository)
    def load_from_disk(self) -> TDDSessionState
    def update(self, event: TDDEvent) -> TDDSessionState  # Auto-calls repository.append_event()
    def get_current_state(self) -> TDDSessionState
    def get_history(self) -> List[str]  # Formatted history

# Global session registry
active_sessions: Dict[str, TDDSession] = {}

def get_or_create_session(session_id: str, repository: TDDSessionRepository) -> TDDSession:
    if session_id not in active_sessions:
        active_sessions[session_id] = TDDSession(session_id, repository)
    return active_sessions[session_id]
```

### MCP Handler Pattern
```python
# Individual handler functions for each MCP tool
def handle_start_session(goal: str, test_files: List[str], ...) -> str:
    # Returns session_id or raises exceptions
    
def handle_next_phase(evidence_description: str) -> TDDSessionState:
    # Returns new state or raises exceptions

def handle_initialize() -> str:
    # Returns comprehensive TDD-MCP usage instructions
    
def handle_start_session_wizard(goal: str) -> str:
    # Returns guided setup prompt for session parameters
    
def handle_quick_help() -> Dict[str, Any]:
    # Returns context-aware shortcuts and commands
    
# Exception-based error handling
class SessionLockedError(Exception): pass
class InvalidSessionError(Exception): pass
class CorruptedDataError(Exception): pass
```

### File Organization
```
Session files: {session_id}.json
Lock files: {session_id}.lock

Lock file content:
{
  "locked_by": "agent_identifier_or_pid", 
  "locked_at": "2025-07-11T10:30:00Z"
}
```

## File & Session Management

### Event Sourcing Architecture
- **Session Storage**: Append-only event stream in JSON format
- **State Calculation**: Current state derived by replaying all events
- **Event Types**: 
  - `session_started`, `session_updated`, `phase_changed`, `rollback`, `log_entry`, `session_paused`, `session_resumed`, `session_ended`
- **Schema Versioning**: Each session file includes schema version for migrations

### Session Persistence
- **Storage Location**: `$TDD_MCP_SESSION_DIR` (default: `$PROJECT_ROOT/.tdd-mcp/sessions/`)
- **Format**: JSON event stream files named by session ID
- **File Paths**: Explicit relative or absolute paths (no glob patterns in v1)
- **Test Execution**: All commands in `run_tests` list must be executed
- **Concurrency**: Lock file mechanism prevents concurrent session access

### Session Event Structure
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
        "run_tests": ["pytest tests/test_auth.py -v"],
        "custom_rules": []
      }
    },
    {
      "timestamp": "2025-07-11T10:35:00Z", 
      "event_type": "phase_changed",
      "data": {
        "from_phase": "write_test",
        "to_phase": "implement", 
        "evidence": "Created failing test for user login validation"
      }
    },
    {
      "timestamp": "2025-07-11T10:37:00Z",
      "event_type": "log_entry", 
      "data": {
        "message": "Added edge case for empty username handling"
      }
    }
  ]
}
```

### Session Lifecycle
- Sessions survive MCP server restarts
- Multiple sessions supported (one active at a time with locking)
- Complete audit trail through event stream

## Rule System

### Global Rules (Built-in)
- Write ONE failing test per cycle
- Write minimal code to make test pass
- Refactor only after tests pass
- Evidence required for phase transitions

### Custom Rules (Per Session)
- Stored in session JSON file
- Examples: "Commit at end of each cycle", "Run linter before refactor"
- Announced at session start/resume
- Reminded at each phase transition
- Cannot override global TDD rules

## Configuration Management

### Environment Variables
- **TDD_MCP_SESSION_DIR**: Custom session storage directory (default: `$PROJECT_ROOT/.tdd-mcp/sessions/`)
- **TDD_MCP_LOG_LEVEL**: Logging verbosity - `debug|info|warn|error` (default: `info`)
- **TDD_MCP_USE_MEMORY_REPOSITORY**: Use in-memory storage for testing (default: `false`)

## Error Handling & Concurrency

### Lock File Mechanism
- Session lock files prevent concurrent access: `{session_id}.lock`
- Lock acquired on session resume/start, released on pause/end
- Clear error messages when session is locked by another agent

### Error Response Format
- Structured error responses sent back to agent
- Error types: `session_locked`, `invalid_session`, `corrupted_data`, `file_not_found`
- Include recovery suggestions in error messages

## Agent Guidance & Prompt System

### Initialize Prompt
The `initialize()` tool returns comprehensive guidance for agents new to TDD-MCP:

```
🔄 TDD-MCP Server Ready

You now have access to a Test-Driven Development workflow management system. Here's how to use it effectively:

## WORKFLOW OVERVIEW
TDD follows a strict 3-phase cycle:
1. 📝 WRITE_TEST: Write ONE failing test
2. ✅ IMPLEMENT: Write minimal code to make the test pass  
3. 🔧 REFACTOR: Improve code/tests (optional, can be skipped)

## ESSENTIAL TOOLS
• start_session() - Begin new TDD session with goals and file specifications
• get_current_state() - Check what phase you're in and what to do next
• next_phase(evidence) - Move forward with evidence of what you accomplished
• rollback(reason) - Go back one phase if you need to change approach
• log(message) - Add contextual notes without affecting workflow state
• history() - View complete session timeline

## GETTING STARTED
1. Always call get_current_state() first to check for existing sessions
2. If no active session, use start_session() with clear goals
3. Follow the suggested_next_action from get_current_state()
4. Provide evidence when calling next_phase() - explain what you did

## BEST PRACTICES  
• Write tests in allowed test_files only during WRITE_TEST phase
• Write implementation in allowed implementation_files only during IMPLEMENT phase
• Always provide clear evidence when transitioning phases
• Use log() to document your thinking and decisions
• Check get_current_state() frequently for guidance

## QUICK COMMANDS
To help user manage sessions efficiently:
• "next" → You call next_phase() with evidence
• "rollback" → You call rollback() with reason  
• "status" → You call get_current_state()
• "log X" → You call log() with message X

The system enforces TDD discipline - embrace the constraints for better code quality!
```

### Quick Help System
The `quick_help()` tool provides context-aware shortcuts:

```python
# Returns dynamic help based on current session state
{
  "current_context": "write_test phase, cycle 2",
  "available_actions": [
    "Write a failing test in: tests/test_auth.py",
    "Call next_phase('wrote failing test for login validation') when done",
    "Use log('added edge case consideration') for notes"
  ],
  "quick_commands": {
    "next": "next_phase(evidence_description)",
    "rollback": "rollback(reason)", 
    "status": "get_current_state()",
    "log": "log(message)",
    "pause": "pause_session()"
  },
  "workflow_reminders": [
    "Write only ONE test per cycle",
    "Test should fail before moving to implement phase"
  ]
}
```

### User Command Shortcuts
For efficient user-agent interaction, the system recognizes these natural language patterns:

**Session Management:**
- "start TDD session for [goal]" → Agent calls start_session()
- "what's the current status?" → Agent calls get_current_state()
- "show me the history" → Agent calls history()
- "pause this session" → Agent calls pause_session()

**Phase Transitions:**
- "next" or "move to next phase" → Agent calls next_phase() with evidence
- "go back" or "rollback" → Agent calls rollback() with reason
- "skip refactor" → Agent calls next_phase() from refactor to write_test

**Logging & Documentation:**
- "log that [message]" → Agent calls log() with the message
- "note: [observation]" → Agent calls log() with the observation

### Contextual Prompts by Phase

**WRITE_TEST Phase:**
```
📝 WRITE_TEST PHASE (Cycle {cycle_number})

Your task: Write ONE failing test for the current goal
Allowed files: {test_files}
Current goal: {goal}

Guidelines:
• Focus on a single behavior or requirement
• Test should fail initially (red phase)
• Use descriptive test names that explain the behavior
• Keep tests simple and focused

When you've written the failing test:
next_phase("wrote failing test for [specific behavior tested]")
```

**IMPLEMENT Phase:**
```
✅ IMPLEMENT PHASE (Cycle {cycle_number})

Your task: Write minimal code to make the failing test pass
Allowed files: {implementation_files}
Test commands: {run_tests}

Guidelines:
• Write the simplest code that makes the test pass
• Don't over-engineer - just make it green
• Focus on the specific test case, not general solutions

When the test passes:
next_phase("implemented [specific functionality] to make test pass")
```

**REFACTOR Phase:**
```
🔧 REFACTOR PHASE (Cycle {cycle_number})

Your task: Improve code quality without changing behavior
Allowed files: {test_files} + {implementation_files}

Options:
• Refactor implementation code for clarity/efficiency
• Merge or improve test cases if needed
• Skip if no refactoring needed

When done refactoring:
next_phase("refactored [specific improvements made]")

To skip refactoring:
next_phase("no refactoring needed, moving to next test")
```

## Agent Integration

### Context Provision
- No special system prompts required - all guidance provided via MCP tools
- Rules announced at session start/resume via contextual prompts
- Phase-specific guidance in `get_current_state()` responses
- Evidence-based transitions with `next_phase(evidence_description)`
- Rich session history available via `history()` tool
- `initialize()` tool provides comprehensive onboarding for new agents
- `quick_help()` offers context-aware shortcuts and reminders

### User-Agent Collaboration
- Natural language command recognition for efficient interaction
- Contextual prompts adapt to current phase and cycle number
- Built-in shortcuts reduce cognitive load for users
- Clear guidance helps agents follow TDD discipline without confusion
- Evidence requirements ensure thoughtful phase transitions

### Error Handling Philosophy
- User/agent responsible for handling test failures, malformed code
- MCP server focuses on workflow enforcement, not file validation
- Pause/resume or session restart for error recovery
- Clear structured error responses for system-level issues

## Non-Functional Requirements

### Event-Based Logging
- All events stored in append-only event stream
- `log()` tool for agent to add contextual information
- `history()` tool provides formatted timeline of session progress
- Complete audit trail for debugging and review
- Phase transitions, rollbacks, and user logs all tracked

### Performance
- Minimal latency for state queries via event replay
- Efficient JSON serialization/deserialization
- Lock file mechanism for safe concurrent operations
- Support for large session histories through efficient event processing

### Context Provision
- No special system prompts required
- Rules announced at session start/resume
- Phase-specific guidance in `get_current_state()`
- Evidence-based transitions with `next_phase(evidence_description)`

### Error Handling Philosophy
- User/agent responsible for handling test failures, malformed code
- MCP server focuses on workflow enforcement, not validation
- Pause/resume or session restart for error recovery

## Non-Functional Requirements

### Logging
- All phase transitions logged with timestamps and evidence
- Session creation, pause, resume, end events tracked
- Rule violations and rollbacks recorded
- Debug logs for troubleshooting workflow issues

### Performance
- Minimal latency for state queries
- Efficient JSON serialization/deserialization
- Support for large session histories

## Project Structure & Packaging

### Package Organization
```
tdd_mcp/
├── __init__.py
├── main.py                    # FastMCP server entry point
├── handlers/                  # MCP tool handlers
│   ├── __init__.py
│   ├── session_handlers.py    # start_session, update_session, etc.
│   ├── workflow_handlers.py   # next_phase, rollback, get_current_state
│   ├── logging_handlers.py    # log, history
│   └── guidance_handlers.py   # initialize, quick_help
├── domain/                    # Core business logic
│   ├── __init__.py
│   ├── session.py            # TDDSession class
│   ├── events.py             # Event schemas and TDDEvent
│   └── exceptions.py         # Custom exception classes
├── repository/                # Data persistence layer
│   ├── __init__.py
│   ├── base.py               # Abstract TDDSessionRepository
│   └── filesystem.py         # FileSystemRepository implementation
└── utils/                     # Supporting utilities
    ├── __init__.py
    ├── config.py             # Environment variable handling
    └── logging.py            # Logging configuration
```

### PyPI Distribution
- Package name: `tdd-mcp`
- Entry point: `tdd-mcp` command for starting server (points to `tdd_mcp.main:start_server`)
- `pyproject.toml` with `uv` build system
- Minimal dependencies: FastMCP V2, Pydantic
- Python 3.12+ requirement

---

## Architecture Highlights

### Event Sourcing Benefits
- **Complete Audit Trail**: Every action, phase change, and log entry preserved
- **Rollback Capability**: `rollback()` adds new events rather than modifying state
- **Debugging**: Full session history available for troubleshooting
- **Consistency**: Current state always calculated from authoritative event stream
- **Future-Proof**: New event types can be added without breaking existing sessions

### Prompt System Benefits
- **Zero Configuration**: Agents learn TDD-MCP usage without special system prompts
- **Contextual Guidance**: Phase-specific instructions reduce confusion and errors
- **Natural Interaction**: Users can give simple commands like "next" or "rollback"
- **Progressive Disclosure**: Initialize provides full overview, quick_help gives contextual shortcuts
- **Workflow Enforcement**: Built-in prompts reinforce TDD discipline and best practices

### State Calculation
Current session state derived by replaying events in chronological order:
1. Start with empty state
2. Apply each event to update state variables
3. Return final calculated state to agent
4. Lock mechanism ensures state consistency during replay

## Next Steps for Implementation

### Phase 1: Core Infrastructure (TDD Approach)
1. **Project Setup**: Initialize `uv` project with `pyproject.toml` and test framework
2. **Event System**: 
   - Write tests for Pydantic event schemas first
   - Implement TDDEvent envelope with validation
   - Test event serialization/deserialization
3. **Repository Layer**: 
   - Write tests for abstract repository interface
   - Test-drive filesystem implementation
   - Test lock file creation and detection
4. **Session Management**: 
   - Write tests for event replay logic
   - Test-drive TDDSession class with state calculation
   - Test phase transition rules and validation
5. **Exception Handling**: 
   - Test custom exception scenarios
   - Verify error messages and recovery paths

### Phase 2: MCP Integration (TDD Approach)
1. **FastMCP Setup**: 
   - Test server configuration and tool registration
   - Mock MCP interactions for testing
2. **Handler Implementation**: 
   - Write tests for each handler function first
   - Test-drive session management integration
   - Test error handling and edge cases
3. **Session Registry**: 
   - Test concurrent session access scenarios
   - Test-drive global session management
   - Test lock file coordination
4. **Prompt System**: 
   - Test prompt generation for different phases
   - Test-drive context-aware help system
5. **Configuration**: 
   - Test environment variable handling
   - Test configuration validation

### Phase 3: Integration & Polish
1. **End-to-End Testing**: Complete workflow testing with mock agents
2. **Error Scenario Testing**: Corruption recovery, invalid states, edge cases
3. **Performance Testing**: Large session replay, concurrent access
4. **Documentation**: Usage examples, tool descriptions, installation guide

### Phase 4: Distribution
1. **PyPI Package**: Build and publish with `uv`
2. **CLI Entry Point**: `tdd-mcp` command for easy server startup
3. **Version Management**: Schema versioning and migration strategy

**TDD Philosophy**: Practice what we preach - write failing tests first, then implement to make them pass, then refactor. This ensures the TDD-MCP server itself is built with the discipline it aims to enforce!