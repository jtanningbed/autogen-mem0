"""
Base agent implementations extending core BaseAgent.
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from ...core.agents import BaseAgent
from ...core.messaging import (
    BaseMessage,
    ChatMessage,
    TaskMessage,
    SystemMessage,
    MessageType,
    TaskStatus
)
from ...core.orchestrator import Orchestrator
from autogen_core.components import message_handler
from autogen_core.components.tools import Tool, ToolSchema
from autogen_core.components.models import FunctionExecutionResult


class BaseToolAgent(BaseAgent):
    """Base class for tool-enabled agents."""
    
    def __init__(
        self,
        agent_id: AgentId,
        name: str,
        description: str,
        tools: List[Tool],
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Initialize tool agent.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            description: Agent description
            tools: List of available tools
            system_prompt: Optional system prompt
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            tools=tools,
            system_prompt=system_prompt,
            **kwargs
        )


class BaseUserProxyAgent(BaseAgent):
    """
    Base class for user proxy agents.
    Provides core functionality for human interaction and message handling.
    """

    def __init__(
        self,
        agent_id: AgentId,
        name: str = "User",
        description: str = "User proxy agent for human interaction",
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            **kwargs
        )
        self.message_history: List[Dict[str, Any]] = []

    @abstractmethod
    async def get_user_input(self, prompt: str = "Your response: ") -> str:
        """Get input from user. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def display_message(self, message: str) -> None:
        """Display message to user. Must be implemented by subclasses."""
        pass
