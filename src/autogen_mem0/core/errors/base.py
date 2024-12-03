"""
Custom exceptions for autogen-mem0.
"""

class AutogenError(Exception):
    """Base exception class for autogen-mem0."""
    pass

class FileOperationError(AutogenError):
    """Raised when a file operation fails."""
    pass

class ShellExecutionError(AutogenError):
    """Raised when a shell command execution fails."""
    pass

class WebBrowserError(AutogenError):
    """Raised when a web browser operation fails."""
    pass

class APIError(AutogenError):
    """Raised when an API call fails."""
    pass

class AnthropicError(APIError):
    """Raised when an Anthropic API operation fails."""
    pass

class ConfigurationError(AutogenError):
    """Raised when there is a configuration error."""
    pass

class ValidationError(AutogenError):
    """Raised when validation fails."""
    pass

class MemoryError(AutogenError):
    """Raised when a memory operation fails."""
    pass

class AgentError(AutogenError):
    """Raised when an agent operation fails."""
    pass

class MessageError(AutogenError):
    """Raised when a message operation fails."""
    pass

class ToolError(AutogenError):
    """Raised when a tool operation fails."""
    pass

class RuntimeError(AutogenError):
    """Raised when a runtime operation fails."""
    pass

class OrchestrationError(AutogenError):
    """Raised when an orchestration operation fails."""
    pass
