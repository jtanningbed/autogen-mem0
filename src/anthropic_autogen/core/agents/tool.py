"""
Tool agent implementations with optional memory capabilities.
"""

from typing import Any, Dict, List, Optional, Union

from autogen_core.base import AgentId, MessageContext
from autogen_core.components.tools import Tool

from .base import BaseAgent, MemoryAgent, ConversationalAgent
from ..messaging import ToolMessage as Message


class BaseToolAgent(BaseAgent):
    """Base tool agent without memory capabilities."""
    
    def __init__(
        self,
        agent_id: AgentId,
        name: str,
        description: str,
        tools: Optional[List[Tool]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Initialize tool agent.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            description: Agent description
            tools: Optional list of available tools
            system_prompt: Optional system prompt
            **kwargs: Additional configuration
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            tools=tools,
            system_prompt=system_prompt,
            **kwargs
        )
        
    async def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        context: MessageContext
    ) -> Any:
        """Execute a tool with the given arguments.
        
        Args:
            tool_name: Name of tool to execute
            tool_args: Tool arguments
            context: Message context
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
            
        tool = self.tools[tool_name]
        return await tool.execute(tool_args, context)


class MemoryToolAgent(MemoryAgent, BaseToolAgent):
    """Tool agent with memory capabilities."""
    
    def __init__(
        self,
        agent_id: AgentId,
        name: str,
        description: str,
        memory_store: Optional[Any] = None,
        tools: Optional[List[Tool]] = None,
        **kwargs
    ):
        """Initialize memory-enabled tool agent.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            description: Agent description
            memory_store: Optional memory storage backend
            tools: Optional list of available tools
            **kwargs: Additional configuration
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            memory_store=memory_store,
            tools=tools,
            **kwargs
        )
        
    async def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        context: MessageContext
    ) -> Any:
        """Execute a tool with memory integration.
        
        Args:
            tool_name: Name of tool to execute
            tool_args: Tool arguments
            context: Message context
            
        Returns:
            Tool execution result
        """
        # Store tool execution
        await self.remember(
            content={
                "tool": tool_name,
                "args": tool_args
            },
            memory_type="tool_execution",
            metadata={"context": context.dict()}
        )
        
        # Execute tool
        result = await super().execute_tool(tool_name, tool_args, context)
        
        # Store result
        await self.remember(
            content=result,
            memory_type="tool_result",
            metadata={
                "tool": tool_name,
                "args": tool_args,
                "context": context.dict()
            }
        )
        
        return result


class ConversationalToolAgent(ConversationalAgent, BaseToolAgent):
    """Tool agent with conversation and memory capabilities."""
    
    def __init__(
        self,
        agent_id: AgentId,
        name: str,
        description: str,
        memory_store: Optional[Any] = None,
        tools: Optional[List[Tool]] = None,
        **kwargs
    ):
        """Initialize conversational tool agent.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            description: Agent description
            memory_store: Optional memory storage backend
            tools: Optional list of available tools
            **kwargs: Additional configuration
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            memory_store=memory_store,
            tools=tools,
            **kwargs
        )
