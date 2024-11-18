"""
Git operations tool implementation.
"""

from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import asyncio
import logging
import subprocess
from pydantic import BaseModel

from ...core.tools import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class GitResult(BaseModel):
    """Result of a Git operation."""
    command: str
    output: str
    status: int


class GitOperations(BaseTool):
    """Tool for performing Git operations."""
    
    def __init__(
            self,
            name: str,
            description: str,
            return_type: type[BaseModel],
            **kwargs
        ):
        """Initialize Git operations tool.
        
        Args:
            name: Tool name
            description: Tool description
            return_type: Return type class
            **kwargs: Additional configuration
        """
        super().__init__(name=name, description=description, return_type=return_type)
    
    async def execute(
            self,
            command: str,
            repo_path: Union[str, Path],
            **kwargs
        ) -> ToolResult:
        """Execute a Git command.
        
        Args:
            command: Git command to execute
            repo_path: Path to Git repository
            **kwargs: Additional command arguments
            
        Returns:
            ToolResult: Command execution result with:
                - success: Whether command succeeded
                - output: Command output
                - error: Error message if command failed
                - metadata: Additional command information
        """
        try:
            repo_path = Path(repo_path)
            if not repo_path.exists():
                return ToolResult(
                    success=False,
                    output=[],
                    error=f"Repository path does not exist: {repo_path}"
                )
            
            # Split command into parts
            cmd_parts = ["git"] + command.split()
            
            # Add any additional arguments
            cmd_parts.extend(kwargs.get("args", []))
            
            # Run Git command
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = GitResult(
                command=command,
                output=stdout.decode() if stdout else stderr.decode(),
                status=process.returncode
            )
            
            return ToolResult(
                success=process.returncode == 0,
                output=result.model_dump(),
                metadata={"command": command}
            )
            
        except Exception as e:
            logger.exception("Git command failed")
            return ToolResult(
                success=False,
                output=[],
                error=str(e)
            )
