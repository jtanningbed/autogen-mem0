from abc import ABC, abstractmethod
from typing import Optional, Set, List
from pydantic import BaseModel

from autogen_core.base import AgentId, CancellationToken
from ..messaging import Message, MessageCategory, MessageQueue
from ..tools import BaseTool

class AgentState(BaseModel):
    """Base state for all agents"""
    agent_id: str
    name: str
    status: str = "idle"
    metadata: dict = {}

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(
        self,
        agent_id: AgentId,
        name: str,
        message_queue: MessageQueue,
        tools: Optional[List[BaseTool]] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self._message_queue = message_queue
        self._tools = tools or []
        self._state = AgentState(
            agent_id=str(agent_id),
            name=name
        )

    @property
    def state(self) -> AgentState:
        """Get agent state"""
        return self._state

    @abstractmethod
    async def handle_message(
        self,
        message: Message,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """Handle incoming message"""
        pass

    async def send_message(
        self,
        message: Message,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """Send a message"""
        message.sender = self.agent_id
        await self._message_queue.publish(message, cancellation_token)

    async def start(self) -> None:
        """Start the agent"""
        # Subscribe to relevant message categories
        await self._message_queue.subscribe(
            self.agent_id,
            self.get_subscribed_categories()
        )
        
        self._state.status = "running"

    async def stop(self) -> None:
        """Stop the agent"""
        await self._message_queue.unsubscribe(self.agent_id)
        self._state.status = "stopped"

    @abstractmethod
    def get_subscribed_categories(self) -> Set[MessageCategory]:
        """Get message categories this agent subscribes to"""
        pass

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return next((t for t in self._tools if t.name == name), None)

    def save_state(self) -> dict:
        """Save agent state"""
        return self._state.model_dump()

    def load_state(self, state: dict) -> None:
        """Load agent state"""
        self._state = AgentState.model_validate(state)
