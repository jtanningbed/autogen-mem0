# Agent System Documentation

## Overview

Our agent system extends and augments AutoGen's agent framework with enhanced memory capabilities through mem0 integration. We support both event-driven asynchronous workflows through our EventAgent (extending AutoGen's RoutedAgent) and sequential conversational workflows through our memory-enabled agents (extending AutoGen's AssistantAgent).

## Core Components

### Agent Hierarchy

```python
from autogen_core.components import RoutedAgent
from autogen_agentchat import AssistantAgent
from anthropic_autogen.core.agents import (
    EventAgent,           # Async event-driven workflows
    BaseMemoryAgent,      # Memory-enabled sequential workflows
    MemoryEnabledAssistant  # Full featured conversational agent
)
```

### Event-Driven Agents

#### EventAgent
- Extends: `autogen_core.components.RoutedAgent`
- Purpose: Asynchronous event-driven workflows
- Features:
  - Pub/sub messaging
  - Non-sequential execution
  - Event routing
  - Parallel workflow orchestration

### Conversational Agents

#### BaseMemoryAgent
- Extends: `autogen_agentchat.AssistantAgent`
- Purpose: Sequential task-driven workflows
- Features:
  - Memory integration via mem0
  - Follows ChatAgent protocol
  - Sequential conversation handling
  - Task decomposition

#### MemoryEnabledAssistant
- Extends: `BaseMemoryAgent`
- Purpose: Advanced conversational workflows
- Features:
  - Enhanced memory capabilities
  - Group chat patterns
  - Conversable interface
  - Task specialization

## Message Adapter System

The message adapter system provides a flexible way to convert between different message formats in the system. It follows the adapter pattern with a clear hierarchy and factory pattern for management.

### Core Components

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')
U = TypeVar('U')

class MessageAdapter(ABC, Generic[T, U]):
    """Base adapter interface for converting between message types."""
    
    @abstractmethod
    def adapt(self, message: T) -> U:
        """Convert from source type T to target type U."""
        pass

class AutogenMessageAdapter(MessageAdapter[ChatMessage, AutogenChatMessage]):
    """Converts our messages to autogen_agentchat messages.
    The entrypoint for our autogen_agentchat integration."""
    
    def adapt(self, messages: List[ChatMessage]) -> List[AutogenChatMessage]:
        """Convert our message to autogen message format."""
        pass

class AnthropicRequestAdapter(MessageAdapter[List[CoreLLMMessage], List[Dict[str, Any]]]):
    """Converts autogen_core messages to Anthropic API format."""
    pass

class AnthropicResponseAdapter(MessageAdapter[AnthropicMessage, CreateResult]):
    """Converts Anthropic API responses to autogen_core CreateResult."""
    pass
```

### Factory Pattern

```python
class MessageAdapterFactory:
    """Factory for creating message adapters."""
    
    _adapters: Dict[str, MessageAdapter] = {}
    
    @classmethod
    def register(cls, source_type: str, target_type: str, adapter: MessageAdapter) -> None:
        """Register an adapter for source -> target type conversion."""
        cls._adapters[f"{source_type}->{target_type}"] = adapter
    
    @classmethod
    def get_adapter(cls, source_type: str, target_type: str) -> Optional[MessageAdapter]:
        """Get adapter for source -> target type conversion."""
        return cls._adapters.get(f"{source_type}->{target_type}")
```

### Usage in Agents

```python
class MemoryEnabledAssistant(AssistantAgent):
    async def on_messages(
        self,
        messages: Sequence[AutogenChatMessage|AgentMessage],
        cancellation_token: CancellationToken
    ) -> Response:
        """Process messages with memory integration."""
        # Convert any of our message types to autogen format
        autogen_messages = []
        for msg in messages:
            if isinstance(msg, Message):
                autogen_msg = MessageAdapterFactory.adapt(
                    msg,
                    source_type="agent",
                    target_type="autogen"
                )
                autogen_messages.append(autogen_msg)
            else:
                autogen_messages.append(msg)
                
        return await super().on_messages(autogen_messages, cancellation_token)
```

### Message Flow

1. **Agent Input**
   - Messages enter the system through agent interfaces
   - AutogenMessageAdapter converts to autogen format
   - Messages processed by autogen framework

2. **LLM Communication**
   - AnthropicRequestAdapter prepares messages for API
   - AnthropicResponseAdapter handles API responses
   - Results converted back to autogen format

3. **Memory Operations**
   - Messages stored in original format
   - Adapters handle format conversion for queries
   - Context maintained across conversions

   
## Workflow Patterns

### Event-Driven Workflows
```python
class EventDrivenWorkflow:
    def __init__(self):
        self.event_agent = EventAgent()
        self.subscribers = []
    
    async def publish_event(self, event: str):
        """Publish event to all subscribers."""
        await self.event_agent.publish(event)
```

### Conversational Workflows
```python
class GroupChatWorkflow:
    def __init__(self):
        self.agents = [
            MemoryEnabledAssistant("assistant_1"),
            MemoryEnabledAssistant("assistant_2")
        ]
        self.memory = MemoryManager()
    
    async def start_conversation(self, topic: str):
        """Start a group conversation."""
        pass
```

## Memory Integration

### mem0 Enhancement
```python
class BaseMemoryAgent(AssistantAgent):
    def __init__(self):
        super().__init__()
        self.memory = MemoryManager()  # mem0-based memory
    
    async def process_message(self, message: Message):
        """Process message with memory context."""
        context = await self.memory.get_context()
        return await super().process_message(message, context=context)
```

## Usage Examples

### Event-Driven Pattern
```python
# Create event-driven workflow
event_agent = EventAgent()
worker_agent = EventAgent()

# Subscribe to events
await event_agent.subscribe("task_complete", worker_agent)

# Publish events
await event_agent.publish("task_complete", {"status": "success"})
```

### Group Chat Pattern
```python
# Create conversational workflow
assistant1 = MemoryEnabledAssistant("research")
assistant2 = MemoryEnabledAssistant("writing")

# Start group chat
group_chat = GroupChat(agents=[assistant1, assistant2])
await group_chat.start("Write a research paper")
