from typing import Dict, List, Optional
from uuid import uuid4

from autogen_core.base import AgentId, CancellationToken
from ..core.messaging import MessageQueue, TaskMessage
from ..core.task import TaskManager, TaskContext
from ..core.tools.base import BaseTool
from ..core.agents import BaseAgent

class ToolOrchestrator:
    """Orchestrates tool execution through agents"""
    
    def __init__(self):
        self.message_queue = MessageQueue()
        self.task_manager = TaskManager()
        self._tools: Dict[str, BaseTool] = {}
        self._agents: Dict[AgentId, BaseAgent] = {}

    async def register_tool(self, tool: BaseTool) -> None:
        """Register a tool"""
        self._tools[tool.name] = tool

    async def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent"""
        self._agents[agent.agent_id] = agent
        await agent.start()

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: dict,
        timeout: Optional[float] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> TaskContext:
        """Execute a tool through an agent"""
        if tool_name not in self._tools:
            raise ValueError(f"Tool not found: {tool_name}")

        # Create task
        task = await self.task_manager.create_task(
            owner=next(iter(self._agents.keys())),  # Assign to first available agent
            timeout=timeout
        )

        # Create task message
        message = TaskMessage(
            task_id=task.task_id,
            content={
                "tool": tool_name,
                "input": tool_input
            },
            task_type="tool_execution"
        )

        # Publish message
        await self.message_queue.publish(message, cancellation_token)

        return task

    async def stop(self) -> None:
        """Stop all agents"""
        for agent in self._agents.values():
            await agent.stop()
