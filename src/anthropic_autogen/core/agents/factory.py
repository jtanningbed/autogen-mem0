from typing import Dict, Type, Optional, Any
from .base import BaseAgent
from ..messaging import MessageQueue
from ..task import TaskManager

class AgentFactory:
    """Factory for creating agent instances"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agent_types: Dict[str, Type[BaseAgent]] = {}
        return cls._instance
    
    def register_agent_type(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent type"""
        self._agent_types[name] = agent_class
        
    def create_agent(
        self,
        agent_type: str,
        agent_id: str,
        message_queue: MessageQueue,
        task_manager: TaskManager,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """Create an agent instance"""
        if agent_type not in self._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        agent_class = self._agent_types[agent_type]
        return agent_class(
            agent_id=agent_id,
            message_queue=message_queue,
            task_manager=task_manager,
            **(config or {})
        )

# Global factory instance
factory = AgentFactory()
