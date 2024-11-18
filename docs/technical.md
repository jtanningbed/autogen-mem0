# Technical Architecture

This document outlines the technical architecture of the Anthropic-Autogen framework, which builds upon and extends the Autogen Core framework to provide specialized agents and workflows optimized for Anthropic's Claude models.

## Project Structure

```
src/anthropic_autogen/
├── agents/
│   ├── base/
│   │   ├── tool_agent.py      # BaseToolAgent implementation
│   │   ├── user_proxy.py      # BaseUserProxyAgent implementation
│   │   └── base.py            # Common base agent functionality
│   └── specialized/
│       ├── assistants/        # Specialized assistant implementations
│       │   ├── code_assistant.py
│       │   └── data_analysis_assistant.py
│       └── user_interfaces/   # User interface implementations
│           └── web_ui.py
├── core/
│   ├── agent.py              # Core agent base class
│   ├── messaging.py          # Message system implementation
│   ├── runtime.py            # Runtime system
│   ├── runtime_mixin.py      # Runtime capabilities mixin
│   └── orchestrator.py       # Multi-agent orchestration
├── models/
│   └── anthropic/            # Claude model integration
│       └── chat.py
├── tools/
│   ├── base.py              # Base tool implementations
│   ├── code/                # Code-related tools
│   │   ├── linter.py
│   │   ├── test_runner.py
│   │   └── git_operations.py
│   ├── filesystem/          # Filesystem tools
│   └── shell/              # Shell execution tools
└── memory/
    ├── base.py             # Memory system interfaces
    └── stores/             # Memory storage implementations
        ├── in_memory.py
        └── vector_store.py
```

## Component Overview

```mermaid
graph TD
    subgraph "Runtime Layer"
        RT[Runtime] --> |extends| ART[Autogen AgentRuntime]
        RT --> RM[RuntimeMixin]
        RT --> MS[Memory Store]
    end

    subgraph "Agent Layer"
        BA[BaseAgent] --> |extends| AA[Autogen Agent]
        BA --> RA[Routed Agent]
        
        BTA[BaseToolAgent] --> BA
        BUPA[BaseUserProxyAgent] --> BA
        
        subgraph "Specialized Agents"
            CAA[CodeAssistantAgent] --> BTA
            WUP[WebUIUserProxy] --> BUPA
            WO[WorkflowOrchestrator] --> BA
        end
    end

    subgraph "Messaging Layer"
        BM[BaseMessage] --> |extends| AM[Autogen Message]
        BM --> CM[ChatMessage]
        BM --> TM[TaskMessage]
        BM --> TLM[ToolMessage]
        BM --> SM[SystemMessage]
    end

    subgraph "Tool Layer"
        BT[BaseTool] --> |extends| AT[Autogen Tool]
        BT --> CT[Code Tools]
        BT --> FT[Filesystem Tools]
        BT --> ST[Shell Tools]
    end
end
```

## Core Components

### 1. Runtime System (`core/runtime.py`, `core/runtime_mixin.py`)
- **Runtime**: Extends `autogen_core.base.AgentRuntime`
  - Manages agent lifecycle and messaging
  - Integrates with memory system
  - Handles async operations

- **RuntimeMixin**: 
  - Provides core runtime capabilities
  - Memory management
  - Conversation tracking

### 2. Agent System (`agents/base/`, `agents/specialized/`)
- **BaseAgent** (`core/agent.py`): Extends `autogen_core.base.Agent` and `RoutedAgent`
  - Core message handling
  - Agent lifecycle management
  - Integration with runtime

- **BaseToolAgent** (`agents/base/tool_agent.py`): Extends `BaseAgent`
  - Tool execution capabilities
  - LLM integration
  - Message routing for tools

- **BaseUserProxyAgent** (`agents/base/user_proxy.py`): Extends `BaseAgent`
  - User interaction handling
  - Message history management
  - Interactive capabilities

### 3. Messaging System (`core/messaging.py`)
- **BaseMessage**: Extends Autogen's message system
  - Core message attributes
  - Routing information
  - Content handling

Message Types:
- `ChatMessage`: General communication
- `TaskMessage`: Workflow tasks
- `ToolMessage`: Tool execution
- `SystemMessage`: System controls

### 4. Tool System (`tools/`)
- **BaseTool** (`tools/base.py`): Extends `autogen_core.components.tools.Tool`
  - Tool registration
  - Execution handling
  - Result formatting

Tool Categories:
- Code Tools (`tools/code/`): linting, testing, git operations
- Filesystem Tools (`tools/filesystem/`)
- Shell Tools (`tools/shell/`)
- API Tools (`tools/api/`)

## Multi-Agent Design Patterns

Our framework supports several multi-agent design patterns from Autogen:

### 1. Group Chat Pattern
- Multiple agents share a common message thread
- Sequential turn-taking managed by a Group Chat Manager
- Useful for task decomposition with specialized agents
- Implementation:
  ```python
  class GroupChatMessage(BaseModel):
      body: UserMessage

  class RequestToSpeak(BaseModel):
      pass

  # Group Chat Manager handles turn selection
  @message_handler(MessageType.CHAT)
  async def handle_chat(self, message: ChatMessage, context: MessageContext):
      next_speaker = self.select_next_speaker()
      await self.send_message(RequestToSpeak(), to=next_speaker)
  ```

### 2. Reflection Pattern
- Agents perform iterative refinement through reflection
- Example: Code generation followed by code review
- Implementation:
  ```python
  class CodeReviewTask(BaseModel):
      code: str
      review_criteria: List[str]

  class CodeReviewResult(BaseModel):
      review: str
      approved: bool

  # Reviewer agent provides feedback
  @message_handler(MessageType.TASK)
  async def handle_review(self, message: CodeReviewTask, context: MessageContext):
      review = await self.review_code(message.code)
      await self.send_message(CodeReviewResult(review=review), to=context.sender)
  ```

## Message Flow

1. **Agent Initialization**:
```python
agent = BaseAgent(
    agent_id=AgentId(key="unique_key", type=agent_type),
    name="Agent Name",
    description="Agent Description"
)
```

2. **Message Creation**:
```python
message = ChatMessage(
    content="message content",
    sender=sender_id.key,
    recipient=recipient_id.key
)
```

3. **Message Routing**:
```python
await agent.send_message(message, to=recipient_id)
```

4. **Message Handling**:
```python
@message_handler(MessageType.CHAT)
async def handle_chat(self, message: ChatMessage, context: MessageContext):
    # Handle message
    pass
```

## Runtime Flow

1. **Runtime Creation**:
```python
runtime = Runtime(memory_store=InMemoryStore())
```

2. **Agent Registration**:
```python
await runtime.register(agent_type, agent_factory)
```

3. **Message Processing**:
```python
await runtime.process_message(message)
```

4. **Memory Management**:
```python
await runtime.memory.store(
    MemoryEntry(
        agent_id=agent.id,
        message=message
    )
)
```

## Best Practices

1. **Agent Initialization**:
   - Always use the runtime's agent factory pattern
   - Properly initialize agent IDs with both key and type
   - Use descriptive names and descriptions

2. **Message Handling**:
   - Use properly constructed ChatMessage objects
   - Include sender and recipient information
   - Handle message routing through the runtime

3. **Runtime Management**:
   - Start runtime before agent interactions
   - Properly clean up with runtime.stop()
   - Use async/await consistently

## Current Limitations

1. **Python Version Compatibility**:
   - Designed for Python 3.12+
   - Some compatibility issues with certain Python features

2. **Runtime Constraints**:
   - Single-threaded runtime limitations
   - Message routing complexity

3. **Agent Instantiation**:
   - Strict requirements for agent creation context
   - Complex factory pattern requirements

## Future Improvements

1. **Enhanced Compatibility**:
   - Better Python version compatibility
   - More flexible runtime options

2. **Simplified Architecture**:
   - Streamlined agent creation
   - More intuitive message routing

3. **Extended Features**:
   - Additional specialized agents
   - Enhanced tool system
   - Improved memory management

## Related Documentation

- [README.md](../README.md): Project overview and setup
- [Examples](../examples/): Code examples and usage patterns
- [API Documentation](./api.md): Detailed API reference
