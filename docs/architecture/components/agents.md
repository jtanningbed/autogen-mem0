# Agent System Documentation

## Overview

The agent system in autogen-mem0 extends Microsoft's AutoGen v0.4 with memory capabilities through mem0 integration. Memory operations are primarily performed through tools at the LLM level, with initialization and configuration handled at the agent level.

## Core Components

### Agent Types

```python
from autogen_mem0.core.agents import (
    BaseMemoryAgent,      # Legacy base memory agent (not fully tested)
    MemoryEnabledAssistant  # Primary memory-capable assistant
)
```

## Memory-Enabled Assistant

### Initialization

```python
class MemoryEnabledAssistant(AssistantAgent):
    def __init__(
        self,
        config: AgentConfig,
        model_client: ChatCompletionClient,
        tools: Optional[List[Tool]] = None,
        handoffs: Optional[List[Handoff | str]] = None,
        system_message: str = None
    ):
        # Initialize memory components
        if config.memory_config:
            self._memory_manager = MemoryManager(ConfigManager())
            self._conversation_id = self._memory_manager.start_conversation()
            self._memory = self._memory_manager.get_memory(
                self._agent_name, 
                memory_config=self._memory_config
            )
            
            # Add memory tools
            self._tools.append(StoreMemoryTool(self._memory))
            self._tools.append(RecallMemoryTool(self._memory))
```

### Message Processing

```python
class MemoryEnabledAssistant:
    async def on_messages(
        self,
        messages: Sequence[AutogenChatMessage|AgentMessage],
        cancellation_token: CancellationToken
    ) -> Response:
        # Convert messages to autogen format
        autogen_messages = [
            MessageAdapterFactory.adapt(msg, "agent", "autogen")
            if isinstance(msg, Message)
            else msg
            for msg in messages
        ]
        
        return await super().on_messages(autogen_messages, cancellation_token)
```

## Memory Operations

### Via Tools (Primary Method)

```python
# LLM using memory tools
response = await assistant.on_messages([
    ToolCallMessage(
        tool_name="store_memory",
        tool_input={
            "content": "User preference: dark mode",
            "metadata": {"type": "preference"}
        }
    )
])

# Recalling information
response = await assistant.on_messages([
    ToolCallMessage(
        tool_name="recall_memory",
        tool_input={
            "query": "user preferences",
            "limit": 5
        }
    )
])
```

## System Message Enhancement

The assistant automatically enhances the system message with memory context:

```python
# Base system message
base_message = """You are a helpful AI assistant with memory capabilities..."""

# Enhanced with context
system_message = f"""{base_message}

When using memory tools (store_memory, recall_memory), use:
{context_str}
"""
```

## Resource Management

```python
class MemoryEnabledAssistant:
    def close(self):
        """Cleanup memory resources."""
        if self._memory_manager:
            self._memory_manager.close()

    def __del__(self):
        """Ensure cleanup during garbage collection."""
        self.close()
```

## Best Practices

1. **Memory Operations**
   - Use memory tools for storage/retrieval
   - Let the LLM manage memory operations
   - Provide clear context in system message

2. **Configuration**
   - Initialize memory at agent creation
   - Provide complete context information
   - Handle cleanup properly

3. **Message Handling**
   - Use adapter pattern consistently
   - Let base class handle core functionality
   - Maintain message context

4. **Resource Management**
   - Close memory resources explicitly
   - Clean up in destructor as backup
   - Monitor memory usage

## Note on BaseMemoryAgent

The `BaseMemoryAgent` class exists but is not fully tested and may be outdated. For production use, prefer `MemoryEnabledAssistant` which has been thoroughly tested and maintains memory operations through tools.