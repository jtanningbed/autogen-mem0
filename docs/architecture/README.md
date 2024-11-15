# Architecture Documentation

## Agent Workflow Diagram

The `agent_workflow.mmd` file contains a Mermaid diagram showing the high-level architecture and component relationships of the Anthropic AutoGen system.

Key components:

### Workflow Management
- **WorkflowManager**: Orchestrates the overall execution flow
- **WorkflowExecutor**: Handles sequential execution of steps
- **ParallelExecutor**: Manages concurrent task execution
- **StateStore**: Maintains workflow state

### Agents
- **BaseAgent**: Abstract base class for all agents
- **ChatAgent**: Handles conversational interactions
- **TaskAgent**: Executes specific tasks
- **ClaudeAgent**: Anthropic Claude-specific implementation
- **ToolAgent**: Manages tool execution

### Tools
- **BaseTool**: Abstract base for all tools
- **FileTool**: File system operations
- **ShellTool**: Shell command execution
- **CustomTools**: Extension point for additional tools

### Messaging
- **MessageQueue**: Asynchronous message routing
- **Messages**: Base message types
  - ChatMessage: Agent conversations
  - TaskMessage: Task execution
  - ControlMessage: System control

### Task Management
- **TaskManager**: Handles task lifecycle
- **TaskContext**: Task execution context
- **TaskState**: Task status tracking

## Viewing the Diagram

The Mermaid diagram can be viewed:
1. Directly on GitHub (which renders Mermaid natively)
2. Using the Mermaid CLI tool
3. Through various Mermaid-compatible Markdown viewers

## Color Coding

The diagram uses color coding to indicate component types:
- Pink: Primary workflow components
- Blue: Agent components
- Green: Tool components
