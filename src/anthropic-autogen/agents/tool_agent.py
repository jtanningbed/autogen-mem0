from typing import Optional, List
from ..core.agents.task_agent import TaskAgent
from ..core.tools.base import BaseTool
from ..core.task import TaskContext
from autogen_core.base import CancellationToken

class ToolExecutionAgent(TaskAgent):
    """Agent for executing tools based on tasks"""
    
    def __init__(self, *args, tools: List[BaseTool], **kwargs):
        super().__init__(*args, **kwargs)
        self._tools = {tool.name: tool for tool in tools}
        self.log_prefix = "🔧 tool"

    async def _process_task(
        self,
        task_context: TaskContext,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """Process a tool execution task"""
        try:
            # Extract tool name and input from task content
            tool_name = task_context.content.get("tool")
            tool_input = task_context.content.get("input")
            
            if not tool_name or tool_name not in self._tools:
                raise ValueError(f"Invalid or missing tool: {tool_name}")
                
            tool = self._tools[tool_name]
            
            # Execute tool
            result = await tool.execute(
                tool.input_type(**tool_input),
                cancellation_token
            )
            
            # Store results
            await self._task_manager.complete_task(
                task_context.task_id,
                {"result": result.result, "error": result.error}
            )
            
        except Exception as e:
            await self._task_manager.fail_task(
                task_context.task_id,
                str(e)
            )
