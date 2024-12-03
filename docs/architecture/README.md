# Architecture Documentation

## System Overview

The Anthropic-AutoGen system extends AutoGen's agent framework with enhanced memory capabilities through mem0 integration. We build upon AutoGen's core components while adding specialized features for both event-driven and conversational workflows.

## Core Dependencies

### AutoGen Integration
- Agent base classes:
  - `RoutedAgent`: Powers our event-driven workflows
  - `AssistantAgent`: Foundation for conversational agents
- Message protocols
- Tool execution patterns

### Memory Enhancement
- `mem0`: Memory framework integrated with AutoGen agents
  - Vector storage for semantic search
  - Key-value operations for state
  - Context management

### External Dependencies
- `anthropic`: Anthropic API integration
- Additional utilities:
  - Vector storage
  - Key-value operations
  - HTTP clients

## Component Details

### Memory Layer
- Built on mem0 framework
- Enhances AutoGen agents with:
  ```python
  from mem0 import VectorStore, KeyValueStore, SQLStore
  from anthropic_autogen.core.memory import MemoryManager
  ```

### Agent Layer
- Extends AutoGen's agent classes:
  ```python
  from autogen_core.components import RoutedAgent
  from autogen_agentchat import AssistantAgent
  from anthropic_autogen.core.agents import (
      EventAgent,           # Event-driven workflows
      BaseMemoryAgent,      # Memory-enabled tasks
      MemoryEnabledAssistant  # Full featured agent
  )
  ```
- Message adaptation:
  ```python
  from anthropic_autogen.core.agents import MessageAdapter
  # Synchronizes our messages with AutoGen format
  ```

### Tool Layer
- Compatible with AutoGen's tool protocols:
  ```python
  from autogen_core.components.tools import (
      Tool,
      ToolSchema
  )
  from anthropic_autogen.core.tools import BaseTool
  ```
- Custom tools:
  - FileTool: File operations
  - ShellTool: Command execution
  - WebTool: Web interactions

### Message System
- Custom message types with AutoGen compatibility:
  ```python
  from anthropic_autogen.core.messaging import (
      Message,
      SystemMessage,
      UserMessage,
      AssistantMessage,
      ToolCallMessage,
      ToolCallResultMessage
  )
  ```
- Message synchronization:
  ```python
  # Convert between formats
  our_message = MessageAdapter.from_agent_message(autogen_msg)
  autogen_message = our_message.to_autogen_message()
  ```

## Workflow Patterns

### Event-Driven Workflows
- Powered by EventAgent (extends RoutedAgent)
- Asynchronous pub/sub messaging
- Parallel task execution
- Event orchestration

### Conversational Workflows
- Powered by MemoryEnabledAssistant
- Group chat patterns
- Sequential task execution
- Memory-enhanced interactions

## Component Documentation

Detailed documentation in `components/`:
- [Agents](components/agents.md): AutoGen agent extensions
- [Tools](components/tools.md): Tool system implementation
- [Memory](components/memory.md): mem0 integration

## Design Principles

1. **AutoGen Integration**: 
   - Build on proven agent foundations
   - Maintain protocol compatibility
   - Enhance with memory capabilities

2. **Memory-First**:
   - Seamless mem0 integration
   - Rich context management
   - Multi-scope storage

3. **Tool Integration**:
   - AutoGen tool protocol compatibility
   - Custom tool implementations
   - Extensible framework

4. **Message System**:
   - Bidirectional format conversion
   - Protocol synchronization
   - Type safety

5. **Security**:
   - Memory isolation
   - Access control
   - Tool permissions