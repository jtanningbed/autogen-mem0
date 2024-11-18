"""
Anthropic-Autogen Framework
A modular framework for building autonomous agents with memory and conversation capabilities.
"""

from anthropic_autogen.core import (
    # Agents
    BaseAgent,
    MemoryAgent,
    ConversationalAgent,
    BaseToolAgent,
    MemoryToolAgent,
    ConversationalToolAgent,
    
    # Messages
    MessageCommon,
    ChatMessage,
    TaskMessage,
    ToolMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    
    # Mixins
    MemoryMixin,
    ConversationMixin,
    
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
    
    # Orchestration
    Orchestrator
)

from anthropic_autogen.agents.specialized import (
    CodeAssistantAgent,
    DataAnalysisAssistant
)

from anthropic_autogen.tools import (
    FileSystemManager,
    GitOperations,
    TestRunner,
    Linter,
)

__version__ = "0.1.0"

__all__ = [
    # Core Agents
    "BaseAgent",
    "MemoryAgent",
    "ConversationalAgent",
    "BaseToolAgent",
    "MemoryToolAgent",
    "ConversationalToolAgent",
    # Messages
    "MessageCommon",
    "ChatMessage",
    "TaskMessage",
    "ToolMessage",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    # Mixins
    "MemoryMixin",
    "ConversationMixin",
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
    # Orchestration
    "Orchestrator",
    # Specialized Agents
    "CodeAssistantAgent",
    "DataAnalysisAssistant",
    # Tools
    "FileSystemManager",
    "GitOperations",
    "TestRunner",
    "Linter",
]
