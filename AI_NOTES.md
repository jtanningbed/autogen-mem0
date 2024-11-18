# Autogen Core Reference Guide

## Import Paths
```python
# Core Base Components
from autogen_core.base import (
    MessageContext,
    TopicId,
    AgentType,
    CancellationToken,
    MessageSerializer
)

# Core Application Components
from autogen_core.application import SingleThreadedAgentRuntime

# Core Component Utilities
from autogen_core.components import (
    event,
    rpc,
    message_handler,
    RoutedAgent,
    TypeSubscription
)

# Serialization
from autogen_core.base._serialization import PydanticJsonMessageSerializer
```

## Runtime Integration Patterns

### Agent Registration Flow
1. Create runtime instance:
```python
runtime = SingleThreadedAgentRuntime()
```

2. Register agent using class method:
```python
agent_type = await AgentClass.register(
    runtime,                                    # Runtime instance
    topic_type,                                # Topic type string
    lambda: AgentClass(type_name=topic_type)   # Factory function returning agent instance
)
```

3. Access agent instance:
```python
agent = await runtime.try_get_underlying_agent_instance(agent_type, AgentClass)
```

Key points about registration:
- Uses class method rather than direct runtime registration
- Factory function allows lazy instantiation
- Returns AgentType for future reference
- Topic type is passed to both registration and factory

### Message Routing
1. Messages are routed through `on_message` method
2. Each agent defines message types it handles via `_handles_types`
3. Messages are delivered to specific handlers based on type
4. Topics control message distribution across agents

## Component Schemas

### MessageContext
Required parameters:
```python
MessageContext(
    topic_id: TopicId,      # Topic identifier for routing
    sender: Optional[Any],  # Message sender (can be None)
    is_rpc: bool,          # RPC message flag
    cancellation_token: CancellationToken  # For cancelling operations
)
```

### TopicId
Required parameters:
```python
TopicId(
    topic_type: str,  # Type of topic
    source: str      # Source identifier
)
```

### TypeSubscription
Used for message type registration:
```python
TypeSubscription(
    message_type: Type[Any],
    serializer: MessageSerializer
)
```

### RoutedAgent
Base class providing:
1. Message routing infrastructure
2. Type subscription management
3. Handler registration
4. Topic-based message delivery

## @message_handler Decorator

The `@message_handler` decorator is a crucial integration point that:

1. Automatically registers method as handler for specific message type
2. Provides type-safe message routing
3. Integrates with RoutedAgent.on_message
4. Handles message serialization/deserialization

Example usage:
```python
class MyAgent(BaseAgent):
    @message_handler
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> None:
        # Handler implementation
        pass
```

Key aspects:
- Decorator infers message type from type hints
- Automatically registers handler with agent's routing system
- Ensures type safety during message dispatch
- Integrates with agent's message recording/tracking

## Best Practices

1. Always use `@message_handler` for message handling methods
2. Properly initialize MessageContext with all required fields
3. Use class method register() for agent registration
4. Leverage type hints for automatic message routing
5. Access agent instances through runtime.try_get_underlying_agent_instance
6. Record messages within handlers when needed
7. Use proper serialization for message types
8. Provide factory functions for agent instantiation

## Integration Testing Pattern

1. Create specialized test agents
2. Register using class register() method
3. Send test messages through handlers
4. Verify message routing and handling
5. Check message recording
6. Test type support detection
7. Validate specialized agent behavior
