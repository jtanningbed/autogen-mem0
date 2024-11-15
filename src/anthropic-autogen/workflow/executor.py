from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from autogen_core.base import CancellationToken
from autogen_core.components.workflow import (
    WorkflowContext,
    WorkflowExecutor,
    WorkflowStep
)

from ..core.messaging import MessageQueue, ChatMessage, ChatContent
from ..core.task import TaskManager, TaskContext, TaskState
from ..core.tools.base import BaseTool

@dataclass
class WorkflowStepResult:
    """Result of a workflow step execution"""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class AnthropicWorkflowExecutor(WorkflowExecutor):
    """Executes workflows involving Claude and tools"""
    
    def __init__(
        self,
        message_queue: MessageQueue,
        task_manager: TaskManager,
        tools: Optional[List[BaseTool]] = None
    ):
        self.message_queue = message_queue
        self.task_manager = task_manager
        self.tools = {tool.name: tool for tool in (tools or [])}
        
    async def execute_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        cancellation_token: Optional[CancellationToken] = None
    ) -> WorkflowStepResult:
        """Execute a single workflow step"""
        try:
            # Create task for step
            task = await self.task_manager.create_task(
                owner=context.owner,
                timeout=step.timeout
            )
            
            # Execute based on step type
            if step.type == "chat":
                result = await self._execute_chat_step(step, task, cancellation_token)
            elif step.type == "tool":
                result = await self._execute_tool_step(step, task, cancellation_token)
            else:
                raise ValueError(f"Unknown step type: {step.type}")
                
            return WorkflowStepResult(
                success=True,
                output=result,
                metadata={"task_id": task.task_id}
            )
            
        except Exception as e:
            return WorkflowStepResult(
                success=False,
                output=None,
                error=str(e)
            )
            
    async def _execute_chat_step(
        self,
        step: WorkflowStep,
        task: TaskContext,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        """Execute a chat step"""
        try:
            # Create chat message
            message = ChatMessage(
                content=ChatContent(text=step.input),
                sender=task.owner,
                recipient=step.target,
                metadata={"task_id": task.task_id}
            )
            
            # Send message and wait for response
            await self.message_queue.publish(message)
            response = await self.message_queue.wait_for_response(
                message.id,
                timeout=step.timeout
            )
            
            if not response:
                raise TimeoutError("No response received")
                
            # Update task state
            await self.task_manager.update_task_state(
                task.task_id,
                TaskState.COMPLETED,
                {"response": response.content.text}
            )
            
            return response.content.text
            
        except Exception as e:
            await self.task_manager.update_task_state(
                task.task_id,
                TaskState.FAILED,
                {"error": str(e)}
            )
            raise
            
    async def _execute_tool_step(
        self,
        step: WorkflowStep,
        task: TaskContext,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        """Execute a tool step"""
        try:
            # Get tool
            tool = self.tools.get(step.tool)
            if not tool:
                raise ValueError(f"Tool not found: {step.tool}")
                
            # Execute tool
            result = await tool.execute(
                input_data=step.input,
                cancellation_token=cancellation_token
            )
            
            if not result.success:
                raise RuntimeError(f"Tool execution failed: {result.error}")
                
            # Update task state
            await self.task_manager.update_task_state(
                task.task_id,
                TaskState.COMPLETED,
                {"result": result.result}
            )
            
            return result.result
            
        except Exception as e:
            await self.task_manager.update_task_state(
                task.task_id,
                TaskState.FAILED,
                {"error": str(e)}
            )
            raise
from typing import Dict, List, Optional, Any, Set
import asyncio
from datetime import datetime

from autogen_core.base import CancellationToken
from autogen_core.components.models import UserMessage

from ..core.messaging import ChatMessage, ChatContent, MessageCategory
from .schema import WorkflowStep, WorkflowState
from ..core.task import TaskState

class AnthropicWorkflowExecutor:
    """Enhanced workflow executor with complete step execution"""
    
    async def _execute_chat_step(
        self,
        step: WorkflowStep,
        task: TaskContext,
        context: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        """Execute a chat interaction step"""
        try:
            # Prepare message content with context variables
            content = step.input.parameters.get("content", "")
            for var in step.input.context_vars:
                if var in context:
                    content = content.replace(f"{{{var}}}", str(context[var]))

            # Create and send chat message
            message = ChatMessage(
                category=MessageCategory.CHAT,
                content=ChatContent(text=content),
                sender=task.owner,
                metadata={"task_id": task.task_id}
            )
            
            await self.message_queue.publish(message, cancellation_token)
            
            # Wait for response with timeout
            async def wait_for_response():
                async for msg in self.message_queue.get_messages(task.owner):
                    if (
                        msg.category == MessageCategory.CHAT 
                        and msg.metadata.get("task_id") == task.task_id
                    ):
                        return msg.content.text
                        
            response = await asyncio.wait_for(
                wait_for_response(),
                timeout=step.timeout or 60.0
            )
            
            return response

        except asyncio.TimeoutError:
            raise TimeoutError(f"Chat step {step.id} timed out")
        except Exception as e:
            raise RuntimeError(f"Chat step {step.id} failed: {str(e)}")

    async def _execute_tool_step(
        self,
        step: WorkflowStep,
        task: TaskContext,
        context: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        """Execute a tool operation step"""
        try:
            tool_name = step.input.parameters.get("tool")
            if not tool_name or tool_name not in self.tools:
                raise ValueError(f"Invalid tool: {tool_name}")
                
            tool = self.tools[tool_name]
            
            # Prepare tool input with context variables
            tool_input = step.input.parameters.get("input", {})
            for var in step.input.context_vars:
                if var in context:
                    tool_input = self._replace_context_var(tool_input, var, context[var])
            
            # Execute tool
            response = await tool.execute(
                tool_input,
                cancellation_token=cancellation_token
            )
            
            if not response.success:
                raise RuntimeError(f"Tool execution failed: {response.error}")
                
            return response.result

        except Exception as e:
            raise RuntimeError(f"Tool step {step.id} failed: {str(e)}")

    def _replace_context_var(self, obj: Any, var: str, value: Any) -> Any:
        """Recursively replace context variables in objects"""
        if isinstance(obj, str):
            return obj.replace(f"{{{var}}}", str(value))
        elif isinstance(obj, dict):
            return {k: self._replace_context_var(v, var, value) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_context_var(item, var, value) for item in obj]
        return obj
from typing import Dict, Any, Optional
from autogen_core.base import CancellationToken
from ..core.orchestration.orchestrator import AgentOrchestrator
from ..core.tools.registry import ToolRegistry

class WorkflowStep:
    """Represents a step in a workflow"""
    def __init__(self, step_id: str, step_type: str, input_params: Dict[str, Any]):
        self.id = step_id
        self.type = step_type
        self.input = input_params

class WorkflowExecutor:
    """Executes workflow steps using agents and tools"""
    
    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        tool_registry: ToolRegistry
    ):
        self.orchestrator = orchestrator
        self.tool_registry = tool_registry
        
    async def execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        """Execute a workflow step"""
        if step.type == "chat":
            return await self._execute_chat_step(step, context, cancellation_token)
        elif step.type == "tool":
            return await self._execute_tool_step(step, context, cancellation_token)
        elif step.type == "parallel":
            return await self._execute_parallel_step(step, context, cancellation_token)
        else:
            raise ValueError(f"Unknown step type: {step.type}")
            
    async def _execute_chat_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        # Create or get Claude agent
        agent_id = f"claude_{step.id}"
        if not self.orchestrator.get_agent(agent_id):
            await self.orchestrator.start_agent(
                "claude",
                agent_id,
                step.input
            )
            
        # Send message and wait for response
        # Implementation details to be added
        pass
        
    async def _execute_tool_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        # Get tool instance
        tool_name = step.input["tool"]
        tool_class = self.tool_registry.get_tool(tool_name)
        if not tool_class:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        # Create tool agent
        agent_id = f"tool_{step.id}"
        if not self.orchestrator.get_agent(agent_id):
            await self.orchestrator.start_agent(
                "tool",
                agent_id,
                {"tool": tool_class()}
            )
            
        # Execute tool
        # Implementation details to be added
        pass
            
    async def _execute_parallel_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        # Implementation details to be added
        pass
