"""
Autogen-Mem0 Framework
A modular framework for building autonomous agents with memory and conversation capabilities.
"""
from autogen_mem0.core.agents._base import (AgentConfig, EventAgent, BaseMemoryAgent, MemoryEnabledAssistant)

from autogen_mem0.core import (
    # Agents
    AgentConfig,
    EventAgent,
    BaseMemoryAgent,
    MemoryEnabledAssistant,
    
    # Messages
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    FinishReasons,
    ChatMessage,
    TextMessage,
    MultiModalMessage,
    ToolCallMessage,
    ToolCallResultMessage,
    HandoffMessage,
    StopMessage,
    AgentMessage,
    MessageRegistry,
    
    # Errors
    AutogenError,
    FileOperationError,
    ShellExecutionError,
    WebBrowserError,
    APIError,
    ConfigurationError,
    ValidationError,
    MemoryError,
    AgentError,
    MessageError,
    ToolError,
    RuntimeError,
    OrchestrationError,
    
    # Configuration
    ConfigManager,
    EnvironmentConfig,
    GlobalConfig,
    
    # Memory
    MemoryManager
)

__version__ = "0.1.0"

__all__ = [
    # Agents
    "AgentConfig",
    "EventAgent",
    "BaseMemoryAgent",
    "MemoryEnabledAssistant",
    
    # Messages
    "Message",
    "SystemMessage",
    "UserMessage",
    "AssistantMessage",
    "FunctionExecutionResult", 
    "FunctionExecutionResultMessage",
    "LLMMessage",
    "FinishReasons",
    "ChatMessage",
    "TextMessage",
    "MultiModalMessage",
    "ToolCallMessage",
    "ToolCallResultMessage",
    "HandoffMessage",
    "StopMessage",
    "AgentMessage",
    "MessageRegistry",
    
    # Errors
    "AutogenError",
    "FileOperationError",
    "ShellExecutionError",
    "WebBrowserError",
    "APIError",
    "ConfigurationError",
    "ValidationError",
    "MemoryError",
    "AgentError",
    "MessageError",
    "ToolError",
    "RuntimeError",
    "OrchestrationError",
    
    # Configuration
    "ConfigManager",
    "EnvironmentConfig",
    "GlobalConfig"
    
    # Memory
    "MemoryManager",
]
