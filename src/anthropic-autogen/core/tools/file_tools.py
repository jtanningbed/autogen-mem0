from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from autogen_core.base import CancellationToken
from .base import BaseTool, ToolResponse

class FileInput(BaseModel):
    """Input for file operations"""
    path: str
    content: Optional[str] = None
    mode: str = "read"  # read, write, append

class FileOutput(BaseModel):
    """Output from file operations"""
    content: Optional[str] = None
    path: str
    success: bool

class FileTool(BaseTool[FileInput, FileOutput, None]):
    """Tool for file operations"""
    
    def __init__(self):
        super().__init__(
            name="file",
            description="Read, write, or append to files",
            input_type=FileInput,
            output_type=FileOutput
        )

    async def execute(
        self,
        input_data: FileInput,
        cancellation_token: Optional[CancellationToken] = None
    ) -> ToolResponse[FileOutput]:
        try:
            path = Path(input_data.path)
            
            if input_data.mode == "read":
                if not path.exists():
                    return ToolResponse(
                        success=False,
                        result=FileOutput(path=str(path), success=False),
                        error="File does not exist"
                    )
                content = path.read_text()
                return ToolResponse(
                    success=True,
                    result=FileOutput(
                        content=content,
                        path=str(path),
                        success=True
                    )
                )
                
            elif input_data.mode in ("write", "append"):
                if input_data.content is None:
                    return ToolResponse(
                        success=False,
                        result=FileOutput(path=str(path), success=False),
                        error="Content required for write/append mode"
                    )
                    
                mode = "a" if input_data.mode == "append" else "w"
                path.parent.mkdir(parents=True, exist_ok=True)
                
                with path.open(mode) as f:
                    f.write(input_data.content)
                    
                return ToolResponse(
                    success=True,
                    result=FileOutput(
                        path=str(path),
                        success=True
                    )
                )
                
            else:
                return ToolResponse(
                    success=False,
                    result=FileOutput(path=str(path), success=False),
                    error=f"Invalid mode: {input_data.mode}"
                )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                result=FileOutput(path=str(path), success=False),
                error=str(e)
            )
