"""Error types for autogen-mem0."""

class MemoryError(Exception):
    """Base class for memory-related errors."""
    pass

class MemoryConfigError(MemoryError):
    """Error in memory configuration."""
    pass

class MemoryStoreError(MemoryError):
    """Error storing data in memory."""
    pass

class MemoryRecallError(MemoryError):
    """Error recalling data from memory."""
    pass

class ToolError(Exception):
    """Base class for tool-related errors."""
    pass

class ToolConfigError(ToolError):
    """Error in tool configuration."""
    pass

class ToolExecutionError(ToolError):
    """Error executing tool."""
    pass

class ToolNotFoundError(ToolError):
    """Tool not found."""
    pass

class AdapterError(Exception):
    """Base class for adapter-related errors."""
    pass

class AdapterConfigError(AdapterError):
    """Error in adapter configuration."""
    pass

class AdapterConversionError(AdapterError):
    """Error converting between message formats."""
    pass