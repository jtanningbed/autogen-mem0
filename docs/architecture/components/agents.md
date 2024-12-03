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

## Message Handling

### Message Adaptation
```python
from anthropic_autogen.core.messaging import MessageAdapter

class MessageAdapter:
    """Synchronizes message formats between our system and AutoGen."""
    
    @classmethod
    def to_autogen_message(cls, message: Message) -> dict:
        """Convert our message to AutoGen format."""
        pass
    
    @classmethod
    def from_autogen_message(cls, message: dict) -> Message:
        """Convert AutoGen message to our format."""
        pass
```

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
