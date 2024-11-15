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
