"""Agent guidance and prompt handlers for TDD-MCP."""

from typing import Dict, List, Any, Optional

from . import session_handlers
from ..domain.exceptions import InvalidSessionError


def handle_start_session_wizard(goal: str) -> str:
    """Start the session wizard and guide the agent through TDD session setup.
    
    Args:
        goal: Initial high-level goal provided by the user
        
    Returns:
        Detailed guidance prompt for collecting TDD session requirements
    """
    return f"""🧙‍♂️ TDD Session Setup Analysis

I want to start a new TDD session on the goal: **{goal}**

But, before we start the session help me clarify the scope and the other parameters for the session_start tool call.

Let's review the current implementation, the provided or mentioned documentation in the current context.
Important: Do not start the session yet, just suggest parameters for the tool call.

## CONTEXT ANALYSIS NEEDED

Please analyze the current workspace and provide your suggestions for:

### 1. REFINED GOAL & DEFINITION OF DONE
Current goal: "{goal}"

**Your task:** Review the current codebase/documentation and suggest:
- A more specific, testable goal statement
- Clear definition of done criteria
- Scope boundaries for this TDD session

### 2. TEST FILES ANALYSIS
**Your task:** Examine the project structure and suggest:
- Specific test file paths that align with the goal
- Whether to create new test files or use existing ones
- Follow the project's existing test organization patterns

### 3. IMPLEMENTATION FILES ANALYSIS  
**Your task:** Analyze the codebase and suggest:
- Target implementation files that need to be created or modified
- Consider the project's architecture and file organization
- Identify dependencies and related modules

### 4. TEST EXECUTION STRATEGY
**Your task:** Review the project setup and suggest:
- Appropriate test commands based on the project's test framework
- Consider existing test configuration (pytest.ini, package.json, etc.)
- Include any necessary setup or environment commands

### 5. CUSTOM RULES ANALYSIS
**Your task:** Based on the project context, suggest:
- Language-specific TDD conventions
- Project-specific coding standards
- Testing framework best practices
- Architecture constraints

## EXPECTED OUTPUT FORMAT

Please provide your analysis in this format:

```
SUGGESTED start_session() PARAMETERS:

goal: "refined goal with clear definition of done"
test_files: ["specific/path/to/test_file.py", "another/test/file.py"]
implementation_files: ["specific/path/to/implementation.py", "another/file.py"]
run_tests: ["pytest path/to/tests/", "additional commands if needed"]
custom_rules: ["rule 1", "rule 2", "rule 3"]
```

**Remember:** Analyze the current context thoroughly before suggesting parameters. 
Don't start the session - just provide the suggested parameters for review."""


def handle_initialize() -> str:
    """Provide comprehensive TDD-MCP usage instructions for new agents.
    
    Returns:
        Comprehensive guidance string for agents new to TDD-MCP
    """
    return """🔄 TDD-MCP Server Ready

You now have access to a Test-Driven Development workflow management system (TDD-MCP). 
Here's how to use this MCP server effectively:

## WORKFLOW OVERVIEW
TDD follows a strict 3-phase cycle:
1. 📝 WRITE_TEST: Write ONE failing test
2. ✅ IMPLEMENT: Write minimal code to make the test pass  
3. 🔧 REFACTOR: Improve code/tests (optional, can be skipped)

## ESSENTIAL MCP TOOLS
• start_session() - Begin new TDD session with goals and file specifications
• get_current_state() - Check what phase you're in and what to do next
• next_phase(evidence) - Move forward with evidence of what you accomplished
• rollback(reason) - Go back one phase if you need to change approach
• log(message) - Add contextual notes without affecting workflow state
• history() - View complete session timeline

## GETTING STARTED
1. Always call the get_current_state() tool first to check for existing sessions
2. If no active session, use start_session() tool with clear goals
3. Follow the suggested_next_action from the get_current_state() tool
4. Provide evidence when calling next_phase() tool - explain what you did

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

## IMPORTANT RULES

- Important: Write only ONE test per cycle!
- Important: Write only the neccessary minimal code to make the one failing test pass!

Let's reply with "Kent Beck is my Hero." to indicate you understand the workflow and ready to begin.

"""


def handle_quick_help() -> Dict[str, Any]:
    """Provide context-aware shortcuts and help based on current session state.
    
    Returns:
        Dictionary with context-aware help and shortcuts
        
    Raises:
        InvalidSessionError: If no active session exists
    """
    try:
        # Try to get current state to provide context-aware help
        from ..handlers.workflow_handlers import handle_get_current_state
        current_state = handle_get_current_state()
        
        # Determine context based on current phase
        context = f"{current_state.current_phase} phase, cycle {current_state.cycle_number}"
        
        # Phase-specific available actions
        available_actions = _get_phase_specific_actions(current_state)
        
        # Phase-specific workflow reminders
        workflow_reminders = _get_phase_reminders(current_state.current_phase)
        
        return {
            "current_context": context,
            "available_actions": available_actions,
            "quick_commands": {
                "next": "next_phase(evidence_description)",
                "rollback": "rollback(reason)", 
                "status": "get_current_state()",
                "log": "log(message)",
                "pause": "pause_session()"
            },
            "workflow_reminders": workflow_reminders
        }
        
    except InvalidSessionError:
        # No active session - provide general help
        return {
            "current_context": "No active session",
            "available_actions": [
                "Start a new session with: start_session(goal, test_files, implementation_files, run_tests, custom_rules)",
                "Resume an existing session with: resume_session(session_id)",
                "Check for existing sessions in your session directory"
            ],
            "quick_commands": {
                "start": "start_session(...)",
                "resume": "resume_session(session_id)",
                "status": "get_current_state()"
            },
            "workflow_reminders": [
                "Always start with a clear goal and definition of done",
                "Specify explicit file paths for tests and implementation",
                "Define how to run your test suite"
            ]
        }


def _get_phase_specific_actions(state) -> List[str]:
    """Get actions available for the current phase.
    
    Args:
        state: Current TDDSessionState
        
    Returns:
        List of phase-specific action descriptions
    """
    if state.current_phase == "write_test":
        return [
            f"Write a failing test in: {', '.join(state.test_files)}",
            "Call next_phase('wrote failing test for [specific behavior tested]') when done",
            "Use log('added edge case consideration') for notes"
        ]
    elif state.current_phase == "implement":
        return [
            f"Write minimal code to make test pass in: {', '.join(state.implementation_files)}",
            f"Run tests with: {', '.join(state.run_tests)}",
            "Call next_phase('implemented [specific functionality] to make test pass') when done"
        ]
    elif state.current_phase == "refactor":
        all_files = state.test_files + state.implementation_files
        return [
            f"Improve code quality in: {', '.join(all_files)}",
            "Call next_phase('refactored [specific improvements made]') when done",
            "Or call next_phase('no refactoring needed, moving to next test') to skip"
        ]
    else:
        return ["Unknown phase - check system state"]


def _get_phase_reminders(phase: str) -> List[str]:
    """Get workflow reminders for the current phase.
    
    Args:
        phase: Current phase name
        
    Returns:
        List of phase-specific reminders
    """
    if phase == "write_test":
        return [
            "Write only ONE test per cycle",
            "Test should fail before moving to implement phase",
            "Focus on a single behavior or requirement"
        ]
    elif phase == "implement":
        return [
            "Write the simplest code that makes the test pass",
            "Don't over-engineer - just make it green",
            "Focus on the specific test case, not general solutions"
        ]
    elif phase == "refactor":
        return [
            "Improve code quality without changing behavior",
            "Tests should still pass after refactoring",
            "Refactoring is optional - can be skipped"
        ]
    else:
        return ["Follow TDD cycle strictly"]