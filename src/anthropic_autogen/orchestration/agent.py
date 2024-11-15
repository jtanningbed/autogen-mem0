from typing import Dict, Optional, Any
from ..core.orchestration.base import BaseOrchestrator
from ..core.orchestration.types import OrchestrationRequest, OrchestrationResult
from ..core.agents import BaseAgent
from ..core.messaging import Message, ChatMessage
from autogen_core.base import AgentId, CancellationToken

class AgentOrchestrator(BaseOrchestrator):
    """Orchestrates agent lifecycle and communication"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._agents: Dict[str, BaseAgent] = {}
        
    async def register_component(self, component: BaseAgent) -> None:
        if not isinstance(component, BaseAgent):
            raise ValueError("Component must be an agent")
        await self.start_agent(component.agent_id, component)
        
    async def unregister_component(self, component_id: str) -> None:
        await self.stop_agent(component_id)
        
    async def execute(
        self,
        request: OrchestrationRequest,
        cancellation_token: Optional[CancellationToken] = None
    ) -> OrchestrationResult:
        if request.action == "start":
            return await self._handle_start(request)
        elif request.action == "stop":
            return await self._handle_stop(request)
        elif request.action == "send":
            return await self._handle_send(request, cancellation_token)
        else:
            raise ValueError(f"Unknown action: {request.action}")
            
    async def _handle_start(self, request: OrchestrationRequest) -> OrchestrationResult:
        try:
            agent = await self.start_agent(
                request.parameters["agent_type"],
                request.parameters["agent_id"],
                request.parameters.get("config")
            )
            return OrchestrationResult(success=True, data={"agent_id": agent.agent_id})
        except Exception as e:
            return OrchestrationResult(success=False, error=str(e))
            
    async def _handle_stop(self, request: OrchestrationRequest) -> OrchestrationResult:
        try:
            await self.stop_agent(request.parameters["agent_id"])
            return OrchestrationResult(success=True)
        except Exception as e:
            return OrchestrationResult(success=False, error=str(e))
            
    async def _handle_send(
        self,
        request: OrchestrationRequest,
        cancellation_token: Optional[CancellationToken]
    ) -> OrchestrationResult:
        try:
            message = ChatMessage(
                content=request.parameters["content"],
                sender=request.parameters["sender"],
                recipient=request.parameters["recipient"]
            )
            await self.message_queue.publish(message, cancellation_token)
            return OrchestrationResult(success=True)
        except Exception as e:
            return OrchestrationResult(success=False, error=str(e))
        
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
