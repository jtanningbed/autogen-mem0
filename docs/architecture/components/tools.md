# Tool System Documentation

## Overview

The tool system in autogen-mem0 extends AutoGen's tool framework with memory-specific operations and enhanced configuration capabilities.

## Core Components

### Base Tool

```python
from autogen_core.components.tools import Tool, ToolSchema
from autogen_mem0.core.tools import BaseTool

class BaseTool(Tool):
    """Base class for all tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.schema = self._build_schema()

    @abstractmethod
    async def execute(
        self,
        **kwargs: Any
    ) -> Any:
        """Execute the tool's functionality."""
        pass

    def _build_schema(self) -> ToolSchema:
        """Build the tool's schema."""
        pass
```

## Memory Tools

### StoreMemoryTool

```python
class StoreMemoryTool(BaseTool):
    """Tool for storing information in memory."""
    
    def __init__(self, memory: Memory):
        super().__init__(
            name="store_memory",
            description="Store information in memory"
        )
        self._memory = memory

    async def execute(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        await self._memory.add(
            messages=content,
            metadata=metadata
        )
        return "Successfully stored in memory"
```

### RecallMemoryTool

```python
class RecallMemoryTool(BaseTool):
    """Tool for retrieving information from memory."""
    
    def __init__(self, memory: Memory):
        super().__init__(
            name="recall_memory",
            description="Recall information from memory"
        )
        self._memory = memory

    async def execute(
        self,
        query: str,
        limit: int = 5
    ) -> List[str]:
        return await self._memory.search(
            query=query,
            limit=limit
        )
```

## Tool Registration

```python
class MemoryEnabledAssistant:
    def __init__(self, config: AgentConfig):
        self._tools = [
            StoreMemoryTool(self._memory),
            RecallMemoryTool(self._memory)
        ]
```

## Tool Execution

### Direct Usage

```python
# Create and use tool directly
tool = StoreMemoryTool(memory)
result = await tool.execute(
    content="Important information",
    metadata={"type": "note"}
)
```

### Through Agent

```python
# Agent using tool
response = await agent.on_messages([
    ToolCallMessage(
        tool_name="store_memory",
        tool_input={
            "content": "Remember this",
            "metadata": {"type": "note"}
        }
    )
])
```

## Tool Development

### Creating New Tools

```python
class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Custom functionality"
        )

    def _build_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "param1": "str",
                "param2": "int"
            }
        )

    async def execute(self, **kwargs) -> Any:
        # Implement custom logic
        pass
```

## Best Practices

1. **Tool Design**
   - Clear, focused functionality
   - Well-defined schemas
   - Proper error handling

2. **Memory Tool Usage**
   - Appropriate metadata
   - Meaningful queries
   - Resource cleanup

3. **Error Handling**
   - Graceful failure
   - Informative messages
   - State cleanup

4. **Performance**
   - Async operations
   - Resource management
   - Caching when appropriate

5. **Security**
   - Input validation
   - Access control
   - Safe execution