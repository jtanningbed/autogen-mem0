"""
Tool agent implementations with optional memory capabilities.
"""

from typing import Any, Dict, List, Optional, Union

from autogen_core.base import AgentId, MessageContext
from autogen_core.components.tools import Tool

from ...core.agents.tool import BaseToolAgent, MemoryToolAgent

from ...core.messaging import (
    ChatMessage,
    TaskMessage,
    ToolMessage
)


class BasicToolAgent(BaseToolAgent):
    """Tool agent that directly executes tools without memory."""
    
    async def on_chat_message(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle chat messages by executing tools."""
        # Extract tool name and args from message
        tool_name = message.content.get("tool")
        tool_args = message.content.get("args", {})
        
        if not tool_name:
            raise ValueError("No tool specified in chat message")
            
        # Execute tool
        result = await self.execute_tool(tool_name, tool_args, ctx)
        
        # Send response
        await self.send_message(
            ToolMessage(
                content={
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                }
            ),
            ctx
        )

    async def on_task_message(self, message: TaskMessage, ctx: MessageContext) -> None:
        """Handle task messages by executing tools."""
        # Extract task details
        task = message.content.get("task")
        tools = message.content.get("tools", [])
        
        if not task or not tools:
            raise ValueError("Task message missing task or tools")
            
        # Execute each tool in sequence
        results = []
        for tool_spec in tools:
            tool_name = tool_spec.get("tool")
            tool_args = tool_spec.get("args", {})
            
            if not tool_name:
                continue
                
            result = await self.execute_tool(tool_name, tool_args, ctx)
            results.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result
            })
            
        # Send response with all results
        await self.send_message(
            ToolMessage(content={"results": results}),
            ctx
        )

    async def on_tool_message(self, message: ToolMessage, ctx: MessageContext) -> None:
        """Handle tool messages by executing tools."""
        # Extract tool details
        tool_name = message.content.get("tool")
        tool_args = message.content.get("args", {})
        
        if not tool_name:
            raise ValueError("No tool specified in tool message")
            
        # Execute tool
        result = await self.execute_tool(tool_name, tool_args, ctx)
        
        # Send response
        await self.send_message(
            ToolMessage(
                content={
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                }
            ),
            ctx
        )


class LLMToolAgent(MemoryToolAgent):
    """Tool agent that uses an LLM to decide which tools to use, with memory capabilities."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        tools: List[Tool],
        llm_client: Any,  # Type will be ChatCompletionClient
        memory_store: Optional[Any] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            tools=tools,
            memory_store=memory_store,
            system_prompt=system_prompt,
            **kwargs
        )
        self.llm_client = llm_client

    async def on_chat_message(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Use LLM to decide which tools to use for chat messages."""
        # Get relevant memories
        memories = await self.recall(
            query=message.content,
            memory_type="tool_execution",
            limit=5
        )
        
        # Use LLM to decide tools
        tools_to_use = await self._select_tools(message, memories)
        
        # Execute tools
        results = []
        for tool_spec in tools_to_use:
            tool_name = tool_spec["tool"]
            tool_args = tool_spec["args"]
            
            result = await self.execute_tool(tool_name, tool_args, ctx)
            results.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result
            })
            
        # Send response
        await self.send_message(
            ToolMessage(content={"results": results}),
            ctx
        )

    async def _select_tools(
        self,
        message: ChatMessage,
        memories: List[Any]
    ) -> List[Dict[str, Any]]:
        """Use LLM to select which tools to use.
        
        Args:
            message: Input chat message
            memories: Relevant memory entries
            
        Returns:
            List of tool specifications to execute
        """
        # TODO: Implement LLM-based tool selection
        raise NotImplementedError()