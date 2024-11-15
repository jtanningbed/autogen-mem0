from typing import Dict, Optional, List, Any
import asyncio
from datetime import datetime

from autogen_core.base import CancellationToken
from ..messaging import MessageQueue, Message, MessageCategory
from ..task import TaskManager, TaskContext
from ..agents import BaseAgent
from .factory import AgentFactory

class AgentOrchestrator:
    """Orchestrates interactions between agents"""
    
    def __init__(
        self,
        message_queue: MessageQueue,
        task_manager: TaskManager
    ):
        self.message_queue = message_queue
        self.task_manager = task_manager
        self.factory = AgentFactory()
        self._agents: Dict[str, BaseAgent] = {}
        self._running = False
        
    async def start_agent(
        self,
        agent_type: str,
        agent_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """Start a new agent"""
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already exists")
            
        agent = self.factory.create_agent(
            agent_type,
            agent_id,
            self.message_queue,
            self.task_manager,
            config
        )
        
        await agent.start()
        self._agents[agent_id] = agent
        return agent
        
    async def stop_agent(self, agent_id: str) -> None:
        """Stop an agent"""
        if agent_id in self._agents:
            await self._agents[agent_id].stop()
            del self._agents[agent_id]
            
    async def start(self) -> None:
        """Start the orchestrator"""
        self._running = True
        
    async def stop(self) -> None:
        """Stop the orchestrator"""
        self._running = False
        for agent in self._agents.values():
            await agent.stop()
        self._agents.clear()
        
    async def send_message(
        self,
        message: Message,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """Send a message to agents"""
        await self.message_queue.publish(message, cancellation_token)
        
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)
        
    def list_agents(self) -> List[str]:
        """List all active agents"""
        return list(self._agents.keys())