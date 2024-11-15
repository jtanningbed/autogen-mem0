from typing import Optional
from pydantic import BaseModel

from autogen_core.base import CancellationToken
from ..core.tools.base import BaseTool, ToolResponse

class BashInput(BaseModel):
    """Input for bash commands"""
    command: str
    working_dir: Optional[str] = None
    timeout: Optional[float] = 60.0

class BashOutput(BaseModel):
    """Output from bash commands"""
    stdout: str
    stderr: str
    return_code: int
    success: bool

class BashTool(BaseTool[BashInput, BashOutput, None]):
    """Tool for executing bash commands"""
    
    def __init__(self):
        super().__init__(
            name="bash",
            description="Execute bash commands",
            input_type=BashInput,
            output_type=BashOutput
        )

    async def execute(
        self,
        input_data: BashInput,
        cancellation_token: Optional[CancellationToken] = None
    ) -> ToolResponse[BashOutput]:
        try:
            # Use existing ShellTool implementation
            from ..core.tools.shell_tool import ShellTool, ShellInput
            
            shell_tool = ShellTool()
            shell_result = await shell_tool.execute(
                ShellInput(
                    command=input_data.command,
                    working_dir=input_data.working_dir,
                    timeout=input_data.timeout
                ),
                cancellation_token
            )

            return ToolResponse(
                success=shell_result.success,
                result=BashOutput(
                    stdout=shell_result.result.stdout,
                    stderr=shell_result.result.stderr,
                    return_code=shell_result.result.exit_code,
                    success=shell_result.result.success
                ),
                error=shell_result.error
            )

        except Exception as e:
            return ToolResponse(
                success=False,
                result=BashOutput(
                    stdout="",
                    stderr=str(e),
                    return_code=-1,
                    success=False
                ),
                error=str(e)
            )
