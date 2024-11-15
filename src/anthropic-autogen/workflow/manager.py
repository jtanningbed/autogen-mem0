from typing import Dict, List, Optional
from ..core.task import TaskManager
from ..core.messaging import MessageQueue
from ..agents.claude_agent import ClaudeAgent
from ..agents.tool_agent import ToolExecutionAgent
from ..core.tools.base import BaseTool
from autogen_core.base import CancellationToken

class WorkflowManager:
    """Manages complex workflows involving Claude and tools"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        system_prompt: str = "",
        tools: Optional[List[BaseTool]] = None
    ):
        self.message_queue = MessageQueue()
        self.task_manager = TaskManager()
        
        # Initialize agents
        self.claude_agent = ClaudeAgent(
            agent_id="claude",
            name="Claude",
            message_queue=self.message_queue,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt
        )
        
        if tools:
            self.tool_agent = ToolExecutionAgent(
                agent_id="tool_executor",
                name="Tool Executor",
                message_queue=self.message_queue,
                task_manager=self.task_manager,
                tools=tools
            )
        
    async def start(self) -> None:
        """Start all agents"""
        await self.claude_agent.start()
        if hasattr(self, 'tool_agent'):
            await self.tool_agent.start()
            
    async def stop(self) -> None:
        """Stop all agents"""
        await self.claude_agent.stop()
        if hasattr(self, 'tool_agent'):
            await self.tool_agent.stop()
            
    async def chat(
        self,
        message: str,
        cancellation_token: Optional[CancellationToken] = None
    ) -> str:
        """Send a chat message and get response"""
        response = await self.claude_agent.chat(
            message,
            cancellation_token=cancellation_token
        )
        return response.content.text if response else ""
