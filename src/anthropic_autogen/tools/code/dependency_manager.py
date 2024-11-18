"""
Dependency manager tool implementation.
"""

from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import asyncio
import logging
import subprocess
from pydantic import BaseModel

from ...core.tools import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class DependencyResult(BaseModel):
    """Result of a dependency management operation."""
    command: str
    output: str
    status: int


class DependencyManager(BaseTool):
    """Tool for managing Python package dependencies."""
    
    def __init__(
            self,
            name: str,
            description: str,
            return_type: type[BaseModel],
            **kwargs
        ):
        """Initialize dependency manager.
        
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
            project_path: Union[str, Path],
            package: Optional[str] = None,
            **kwargs
        ) -> ToolResult:
        """Execute a dependency management command.
        
        Args:
            command: Command to execute (install|uninstall|list|freeze)
            project_path: Path to Python project
            package: Optional package name and version
            **kwargs: Additional command arguments
            
        Returns:
            ToolResult: Command execution result with:
                - success: Whether command succeeded
                - output: Command output
                - error: Error message if command failed
                - metadata: Additional command information
        """
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                return ToolResult(
                    success=False,
                    output=[],
                    error=f"Project path does not exist: {project_path}"
                )
            
            # Build command
            cmd_parts = ["uv"]
            
            if command == "install":
                cmd_parts.extend(["pip", "install"])
                if package:
                    cmd_parts.append(package)
            elif command == "uninstall":
                cmd_parts.extend(["pip", "uninstall", "-y"])
                if package:
                    cmd_parts.append(package)
            elif command == "list":
                cmd_parts.extend(["pip", "list"])
            elif command == "freeze":
                cmd_parts.extend(["pip", "freeze"])
            else:
                return ToolResult(
                    success=False,
                    output=[],
                    error=f"Unknown command: {command}"
                )
            
            # Add any additional arguments
            cmd_parts.extend(kwargs.get("args", []))
            
            # Run command
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=str(project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = DependencyResult(
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
            logger.exception("Dependency management failed")
            return ToolResult(
                success=False,
                output=[],
                error=str(e)
            )
