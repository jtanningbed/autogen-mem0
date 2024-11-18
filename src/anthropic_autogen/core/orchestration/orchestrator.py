"""
Orchestrator for coordinating multiple agents using autogen-core's runtime system.
"""

from typing import Dict, List, Optional, Any, Set, Type, Union
from datetime import datetime
import logging
import asyncio
from contextlib import asynccontextmanager

from autogen_core.base import Agent, AgentId, MessageContext
from autogen_core.application import SingleThreadedAgentRuntime, WorkerAgentRuntime
from autogen_core.components import message_handler

from ..agents.base import BaseAgent
from ..mixins.memory import MemoryMixin
from ..mixins.conversation import ConversationMixin
from ..messaging import (
    ChatMessage,
    TaskMessage,
    ToolMessage,
    UserMessage,
    AssistantMessage
)
from ..errors import AgentError


class Orchestrator(ConversationMixin, BaseAgent):
    """Orchestrator for coordinating multiple agents using autogen-core's runtime system."""
    
    def __init__(
        self,
        agent_id: AgentId,
        name: str = "orchestrator",
        description: str = "Coordinates multiple agents and manages workflows",
        runtime_class: Optional[Type[Union[SingleThreadedAgentRuntime, WorkerAgentRuntime]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Initialize orchestrator.
        
        Args:
            agent_id: Unique agent identifier
            name: Orchestrator name
            description: Orchestrator description
            runtime_class: Optional runtime class to use (SingleThreadedAgentRuntime or WorkerAgentRuntime)
            system_prompt: Optional system prompt
            **kwargs: Additional configuration options
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            **kwargs
        )
        
        runtime_class = runtime_class or SingleThreadedAgentRuntime
        if not issubclass(runtime_class, (SingleThreadedAgentRuntime, WorkerAgentRuntime)):
            raise ValueError("Runtime class must be SingleThreadedAgentRuntime or WorkerAgentRuntime")
            
        self.runtime = runtime_class(**kwargs)
        self.workflows: Dict[str, List[TaskMessage]] = {}
        self._semaphore = asyncio.Semaphore(10)  # Default max parallel tasks
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._registered_agents: Set[str] = set()
        
    async def register_agent(self, agent: Agent) -> None:
        """Register agent with orchestrator.
        
        Args:
            agent: Agent to register
        """
        await self.runtime.register_agent(agent)
        self._registered_agents.add(agent.agent_id)
        
    async def deregister_agent(self, agent_id: str) -> None:
        """Deregister agent from orchestrator.
        
        Args:
            agent_id: ID of agent to deregister
        """
        await self.runtime.deregister_agent(agent_id)
        self._registered_agents.discard(agent_id)
        
    @message_handler
    async def handle_task(
        self,
        message: TaskMessage,
        context: MessageContext
    ) -> Optional[TaskMessage]:
        """Handle incoming task messages.
        
        Args:
            message: Task message
            context: Message context
            
        Returns:
            Optional response message
        """
        if message.workflow_id:
            # Handle workflow task
            await self.delegate(
                task=message,
                agent_id=message.target_agent,
                workflow_id=message.workflow_id,
                workflow_step=message.workflow_step,
                condition=message.condition
            )
        else:
            # Handle direct task
            await self.delegate(
                task=message,
                agent_id=message.target_agent
            )
        return None
        
    async def delegate(
        self,
        task: TaskMessage,
        agent_id: str,
        workflow_id: Optional[str] = None,
        workflow_step: Optional[str] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> None:
        """Delegate a task to an agent.
        
        Args:
            task: Task to delegate
            agent_id: ID of agent to delegate to
            workflow_id: Optional workflow ID
            workflow_step: Optional workflow step identifier
            condition: Optional execution condition
            **kwargs: Additional task parameters
        """
        # Verify agent is registered
        if agent_id not in self._registered_agents:
            raise AgentError(f"Agent {agent_id} not registered with orchestrator")
            
        # Update task with workflow info
        if workflow_id:
            task.workflow_id = workflow_id
            task.workflow_step = workflow_step
            task.condition = condition
            
            if workflow_id not in self.workflows:
                self.workflows[workflow_id] = []
            self.workflows[workflow_id].append(task)
            
        # Store task delegation in runtime memory if available
        if hasattr(self.runtime, "remember"):
            await self.runtime.remember(
                content=task,
                memory_type="delegated_task",
                metadata={
                    "agent_id": agent_id,
                    "workflow_id": workflow_id,
                    "workflow_step": workflow_step,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        # Execute task with semaphore for parallel control
        async with self._semaphore:
            task_coroutine = self.runtime.execute_task(
                task=task,
                agent_id=agent_id,
                **kwargs
            )
            self._running_tasks[task.task_id] = asyncio.create_task(task_coroutine)
            
    async def wait_for_task(self, task_id: str) -> None:
        """Wait for a specific task to complete.
        
        Args:
            task_id: ID of task to wait for
        """
        if task_id in self._running_tasks:
            await self._running_tasks[task_id]
            del self._running_tasks[task_id]
            
    async def wait_for_workflow(self, workflow_id: str) -> None:
        """Wait for all tasks in a workflow to complete.
        
        Args:
            workflow_id: ID of workflow to wait for
        """
        if workflow_id in self.workflows:
            tasks = [
                self.wait_for_task(task.task_id)
                for task in self.workflows[workflow_id]
                if task.task_id in self._running_tasks
            ]
            await asyncio.gather(*tasks)
            
    async def cleanup(self) -> None:
        """Clean up orchestrator resources."""
        # Cancel any running tasks
        for task in self._running_tasks.values():
            task.cancel()
            
        # Clean up runtime
        await self.runtime.cleanup()
        
        await super().cleanup()
