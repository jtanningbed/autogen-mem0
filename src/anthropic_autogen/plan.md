Core Agent Components
Replace BaseAgent with autogen-core agent interfaces
Update ClaudeAgent to extend the appropriate autogen-core base class
Remove our custom ChatAgent implementation
Integrate with autogen-core's message handling patterns
Messaging System
Remove custom MessageQueue implementation
Update message types to use autogen-core's message system
Migrate ChatMessage, TaskMessage, and ControlMessage to use autogen-core equivalents
Update message category handling
Task Management
Remove custom TaskManager
Integrate with autogen-core's task system
Update task states and contexts
Migrate task execution patterns
Tools System
Keep FileTool and ShellTool but update to match autogen-core's tool interfaces
Update tool schema handling
Integrate with autogen-core's tool execution patterns
Factory and Orchestration
Remove custom AgentFactory
Update agent registration to use autogen-core patterns
Integrate with autogen-core's component lifecycle
Update orchestration patterns
CLI and Entry Points
Update CLI to use refactored components
Simplify workflow creation
Update configuration handling