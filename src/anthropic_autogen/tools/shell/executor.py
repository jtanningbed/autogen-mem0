"""
Async shell command executor with advanced features and safety checks.
"""

import asyncio
import shlex
import os
import signal
from typing import Optional, List, Dict, Union, AsyncIterator
from pathlib import Path
import psutil
from datetime import datetime, timedelta

from ...core.tools import BaseTool
from ...core.errors import ShellExecutionError

class ShellExecutor(BaseTool):
    """Async shell command executor with safety features and process management."""
    
    def __init__(
        self,
        workspace_root: Optional[str] = None,
        max_output_size: int = 1024 * 1024,  # 1MB
        timeout: int = 300,  # 5 minutes
        allowed_commands: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None
    ):
        """Initialize shell executor.
        
        Args:
            workspace_root: Optional root directory to restrict operations to
            max_output_size: Maximum size of command output in bytes
            timeout: Default command timeout in seconds
            allowed_commands: Optional whitelist of allowed commands
            blocked_commands: Optional blacklist of blocked commands
        """
        self.workspace_root = Path(workspace_root) if workspace_root else None
        self.max_output_size = max_output_size
        self.timeout = timeout
        self.allowed_commands = set(allowed_commands) if allowed_commands else None
        self.blocked_commands = set(blocked_commands) if blocked_commands else set()
        self._active_processes: Dict[int, asyncio.subprocess.Process] = {}
        super().__init__()
        
    def _validate_command(self, command: str) -> None:
        """Validate command against security rules."""
        cmd = shlex.split(command)[0]
        
        if self.allowed_commands and cmd not in self.allowed_commands:
            raise ShellExecutionError(f"Command '{cmd}' is not in allowed commands list")
            
        if cmd in self.blocked_commands:
            raise ShellExecutionError(f"Command '{cmd}' is blocked")
            
    async def _create_process(
        self,
        command: str,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> asyncio.subprocess.Process:
        """Create and start subprocess with proper configuration."""
        if cwd:
            cwd = str(Path(cwd).resolve())
            if self.workspace_root and not str(cwd).startswith(str(self.workspace_root)):
                raise ShellExecutionError(f"Working directory {cwd} is outside workspace root")
                
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
                preexec_fn=os.setsid  # Create new process group
            )
            self._active_processes[process.pid] = process
            return process
        except Exception as e:
            raise ShellExecutionError(f"Failed to create process: {str(e)}")
            
    async def _cleanup_process(self, process: asyncio.subprocess.Process) -> None:
        """Clean up process and its children."""
        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            
            # Terminate children
            for child in children:
                child.terminate()
            gone, alive = psutil.wait_procs(children, timeout=3)
            
            # Kill remaining children
            for child in alive:
                child.kill()
                
            # Terminate parent
            if parent.is_running():
                parent.terminate()
                parent.wait(timeout=3)
                if parent.is_running():
                    parent.kill()
                    
        except psutil.NoSuchProcess:
            pass  # Process already terminated
        except Exception as e:
            # Log error but don't raise
            print(f"Error cleaning up process {process.pid}: {str(e)}")
        finally:
            self._active_processes.pop(process.pid, None)
            
    async def execute(
        self,
        command: str,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        stream_output: bool = False
    ) -> Union[Dict[str, str], AsyncIterator[str]]:
        """Execute shell command with timeout and streaming support.
        
        Args:
            command: Shell command to execute
            cwd: Working directory for command
            env: Environment variables
            timeout: Command timeout in seconds
            stream_output: If True, stream output as it arrives
            
        Returns:
            If stream_output is False, returns dict with stdout/stderr
            If stream_output is True, returns async iterator of output lines
        """
        self._validate_command(command)
        timeout = timeout or self.timeout
        
        process = await self._create_process(command, cwd, env)
        output_size = 0
        
        async def read_stream(stream: asyncio.StreamReader) -> str:
            nonlocal output_size
            chunks = []
            while True:
                chunk = await stream.read(8192)
                if not chunk:
                    break
                output_size += len(chunk)
                if output_size > self.max_output_size:
                    raise ShellExecutionError("Maximum output size exceeded")
                chunks.append(chunk)
            return b''.join(chunks).decode()
            
        try:
            if stream_output:
                return self._stream_output(process, timeout)
            else:
                stdout_task = asyncio.create_task(read_stream(process.stdout))
                stderr_task = asyncio.create_task(read_stream(process.stderr))
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        asyncio.gather(stdout_task, stderr_task),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    raise ShellExecutionError(f"Command timed out after {timeout} seconds")
                    
                return_code = await process.wait()
                return {
                    'stdout': stdout,
                    'stderr': stderr,
                    'return_code': return_code
                }
                
        except Exception as e:
            raise ShellExecutionError(f"Command execution failed: {str(e)}")
        finally:
            await self._cleanup_process(process)
            
    async def _stream_output(
        self,
        process: asyncio.subprocess.Process,
        timeout: int
    ) -> AsyncIterator[str]:
        """Stream process output line by line."""
        start_time = datetime.now()
        
        async def read_line(stream: asyncio.StreamReader) -> Optional[str]:
            try:
                line = await stream.readline()
                return line.decode().rstrip() if line else None
            except Exception:
                return None
                
        while True:
            if (datetime.now() - start_time) > timedelta(seconds=timeout):
                raise ShellExecutionError(f"Command timed out after {timeout} seconds")
                
            stdout_line = await read_line(process.stdout)
            if stdout_line:
                yield f"stdout: {stdout_line}"
                
            stderr_line = await read_line(process.stderr)
            if stderr_line:
                yield f"stderr: {stderr_line}"
                
            if stdout_line is None and stderr_line is None:
                if process.returncode is not None:
                    break
                await asyncio.sleep(0.1)
                
    async def terminate_all(self) -> None:
        """Terminate all active processes."""
        processes = list(self._active_processes.values())
        for process in processes:
            await self._cleanup_process(process)
