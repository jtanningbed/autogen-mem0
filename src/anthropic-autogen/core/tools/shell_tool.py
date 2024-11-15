import asyncio
from typing import Optional
from pydantic import BaseModel

from autogen_core.base import CancellationToken
from .base import BaseTool, ToolResponse

class ShellInput(BaseModel):
    """Input for shell commands"""
    command: str
    working_dir: Optional[str] = None
    timeout: Optional[float] = 60.0

class ShellOutput(BaseModel):
    """Output from shell commands"""
    stdout: str
    stderr: str
    exit_code: int
    success: bool

class ShellTool(BaseTool[ShellInput, ShellOutput, None]):
    """Tool for executing shell commands"""
    
    def __init__(self):
        super().__init__(
            name="shell",
            description="Execute shell commands",
            input_type=ShellInput,
            output_type=ShellOutput
        )

    async def execute(
        self,
        input_data: ShellInput,
        cancellation_token: Optional[CancellationToken] = None
    ) -> ToolResponse[ShellOutput]:
        try:
            process = await asyncio.create_subprocess_shell(
                input_data.command,
                cwd=input_data.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            if cancellation_token:
                cancellation_token.link_future(process)

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout
                )
            except asyncio.TimeoutError:
                process.terminate()
                return ToolResponse(
                    success=False,
                    result=ShellOutput(
                        stdout="",
                        stderr="Command timed out",
                        exit_code=-1,
                        success=False
                    ),
                    error="Command timed out"
                )

            return ToolResponse(
                success=process.returncode == 0,
                result=ShellOutput(
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    exit_code=process.returncode,
                    success=process.returncode == 0
                )
            )

        except Exception as e:
            return ToolResponse(
                success=False,
                result=ShellOutput(
                    stdout="",
                    stderr=str(e),
                    exit_code=-1,
                    success=False
                ),
                error=str(e)
            )
