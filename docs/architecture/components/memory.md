# Memory System Documentation

## Overview

The memory system integrates mem0 with AutoGen to provide persistent memory capabilities for agents. The system is built around a centralized MemoryManager that handles memory operations and context management.

## Core Components

### Memory Manager

```python
from autogen_mem0.core.memory import MemoryManager
from autogen_mem0.core.config import ConfigManager

class MemoryManager:
    """Manages memory operations and lifecycle."""
    
    def __init__(self, config_manager: ConfigManager):
        self._config = config_manager
        self._memories = {}
        self._conversation_id = None

    def start_conversation(self) -> str:
        """Start a new conversation context."""
        pass

    async def get_memory(self, agent_name: str, memory_config: dict) -> Memory:
        """Get or create memory instance for an agent."""
        pass

    def clear_memory(self, agent_name: str) -> None:
        """Clear an agent's memory."""
        pass
```

### Memory Configuration

```python
from mem0.configs.base import MemoryConfig

config = {
    "provider": "mem0",
    "config": {
        "collection": "conversations",
        "vector_store": {
            "type": "qdrant",
            "config": {...}
        },
        "key_value_store": {
            "type": "redis",
            "config": {...}
        }
    }
}
```

## Memory Operations

### Storing Information

```python
# Store with context
await memory.add(
    messages="User prefers dark mode",
    metadata={
        "user_id": "user123",
        "type": "preference",
        "timestamp": "2024-03-04T12:00:00Z"
    },
    filters={"user_id": "user123"}
)
```

### Retrieving Information

```python
# Search with filters
results = await memory.search(
    query="user preferences",
    filters={"type": "preference"},
    limit=5
)

# Get specific memory
memory = await memory.get(
    memory_id="mem123",
    user_id="user123"
)
```

### Context Management

```python
# Start new conversation
conversation_id = memory_manager.start_conversation()

# Get context
context = {
    "user_id": "user123",
    "agent_id": "assistant",
    "session_id": conversation_id,
    "metadata": {"type": "support_session"}
}
```

## Integration with Agents

### BaseMemoryAgent

```python
class BaseMemoryAgent:
    async def __init__(self, config: AgentConfig):
        self._memory_manager = MemoryManager(ConfigManager())
        self._memory = await self._memory_manager.get_memory(
            self.name,
            config.memory_config
        )

    async def store(
        self, 
        content: Any, 
        metadata: Optional[Dict] = None
    ) -> None:
        """Store content in memory."""
        if self._memory:
            await self._memory.add(
                messages=content,
                metadata=metadata,
                user_id=self.name,
                filters={"user_id": self.name}
            )

    async def recall(
        self, 
        query: str,
        limit: int = 5
    ) -> List[Any]:
        """Recall content from memory."""
        if self._memory:
            return await self._memory.search(
                query=query,
                user_id=self.name,
                filters={"user_id": self.name},
                limit=limit
            )
        return []
```

## Memory Tools

### StoreMemoryTool

```python
from autogen_mem0.core.tools import StoreMemoryTool

class StoreMemoryTool(BaseTool):
    """Tool for storing information in memory."""
    
    async def execute(
        self, content: str, metadata: Dict = None
    ) -> str:
        await self._memory.add(
            messages=content,
            metadata=metadata
        )
        return "Memory stored successfully"
```

### RecallMemoryTool

```python
from autogen_mem0.core.tools import RecallMemoryTool

class RecallMemoryTool(BaseTool):
    """Tool for recalling information from memory."""
    
    async def execute(
        self, query: str, limit: int = 5
    ) -> List[str]:
        results = await self._memory.search(
            query=query,
            limit=limit
        )
        return results
```

## Best Practices

1. **Memory Organization**
   - Use consistent metadata schemas
   - Apply appropriate filters
   - Clean up obsolete memories

2. **Context Management**
   - Start new conversations appropriately
   - Include relevant context in metadata
   - Use conversation IDs for tracking

3. **Tool Usage**
   - Use memory tools for agent access
   - Handle tool errors gracefully
   - Validate inputs and outputs

4. **Performance**
   - Set appropriate limits for recalls
   - Use efficient search queries
   - Monitor memory usage

5. **Security**
   - Validate user access
   - Sanitize stored content
   - Manage memory lifecycle