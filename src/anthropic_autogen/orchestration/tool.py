from typing import Dict, Optional
from ..core.orchestration.base import BaseOrchestrator
from ..core.tools.base import BaseTool
from ..core.task import TaskContext
from ..core.messaging import TaskMessage
from autogen_core.base import CancellationToken

class ToolOrchestrator(BaseOrchestrator):
    """Orchestrates tool execution through agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tools: Dict[str, BaseTool] = {}
        
    async def register_tool(self, tool: BaseTool) -> None:
        """Register a tool"""
        self._tools[tool.name] = tool

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
            owner=next(iter(self._agents.keys())),
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
