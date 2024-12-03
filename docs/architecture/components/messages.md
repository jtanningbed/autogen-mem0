# Message System Documentation

## Overview

The message system in autogen-mem0 uses the adapter pattern to handle conversions between different message formats needed for AutoGen integration, LLM communication, and memory operations.

## Core Components

### Base Message Types

```python
from autogen_mem0.core.messaging import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolCallMessage,
    ToolCallResultMessage
)
```

### Message Adapters

```python
from autogen_mem0.core.adapters.messages import (
    MessageAdapter,
    AutogenMessageAdapter,
    AnthropicRequestAdapter,
    AnthropicResponseAdapter
)
```

## Message Flow

1. **Input Processing**
   - Raw messages converted to base types
   - AutogenMessageAdapter prepares for agent processing

2. **Agent Processing**
   - Messages handled by AutoGen framework
   - Memory operations performed as needed

3. **LLM Communication**
   - AnthropicRequestAdapter prepares API requests
   - AnthropicResponseAdapter handles responses

## Usage Examples

### Basic Message Conversion
```python
# Convert to autogen format
autogen_messages = MessageAdapterFactory.adapt(
    messages,
    source_type="agent",
    target_type="autogen"
)

# Convert for LLM request
llm_messages = MessageAdapterFactory.adapt(
    messages,
    source_type="autogen",
    target_type="anthropic"
)
```

### Memory Integration
```python
# Store messages with context
await memory_manager.store(
    messages=messages,
    context={"conversation_id": "123"}
)

# Recall with search
results = await memory_manager.search(
    query="previous context",
    limit=5
)
```

## Design Principles

1. **Separation of Concerns**
   - Message types focus on data structure
   - Adapters handle conversion logic
   - Factory manages adapter selection

2. **Type Safety**
   - Strong typing throughout system
   - Clear interfaces for conversion
   - Runtime type checking

3. **Extensibility**
   - Easy to add new message types
   - Pluggable adapter system
   - Configurable conversion logic