"""
File system operations manager providing high-level async interface for file operations.
"""

import os
import shutil
import asyncio
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
import aiofiles
import aiofiles.os
import json
import yaml
from datetime import datetime

from ...core.tools import BaseTool
from ...core.errors import FileOperationError

class FileSystemManager(BaseTool):
    """Provides high-level async interface for file system operations."""
    
    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize the file system manager.
        
        Args:
            workspace_root: Optional root directory to restrict operations to
        """
        self.workspace_root = Path(workspace_root) if workspace_root else None
        super().__init__()
        
    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and normalize a path."""
        path = Path(path).resolve()
        if self.workspace_root:
            if not str(path).startswith(str(self.workspace_root)):
                raise FileOperationError(f"Path {path} is outside workspace root {self.workspace_root}")
        return path
        
    async def read_file(self, path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Read contents of a file asynchronously."""
        path = self._validate_path(path)
        try:
            async with aiofiles.open(path, mode='r', encoding=encoding) as f:
                return await f.read()
        except Exception as e:
            raise FileOperationError(f"Failed to read file {path}: {str(e)}")
            
    async def write_file(self, path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """Write content to a file asynchronously."""
        path = self._validate_path(path)
        try:
            async with aiofiles.open(path, mode='w', encoding=encoding) as f:
                await f.write(content)
        except Exception as e:
            raise FileOperationError(f"Failed to write file {path}: {str(e)}")
            
    async def append_file(self, path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """Append content to a file asynchronously."""
        path = self._validate_path(path)
        try:
            async with aiofiles.open(path, mode='a', encoding=encoding) as f:
                await f.write(content)
        except Exception as e:
            raise FileOperationError(f"Failed to append to file {path}: {str(e)}")
            
    async def delete_file(self, path: Union[str, Path]) -> None:
        """Delete a file asynchronously."""
        path = self._validate_path(path)
        try:
            await aiofiles.os.remove(path)
        except Exception as e:
            raise FileOperationError(f"Failed to delete file {path}: {str(e)}")
            
    async def create_directory(self, path: Union[str, Path], exist_ok: bool = True) -> None:
        """Create a directory asynchronously."""
        path = self._validate_path(path)
        try:
            await asyncio.to_thread(os.makedirs, path, exist_ok=exist_ok)
        except Exception as e:
            raise FileOperationError(f"Failed to create directory {path}: {str(e)}")
            
    async def delete_directory(self, path: Union[str, Path], recursive: bool = False) -> None:
        """Delete a directory asynchronously."""
        path = self._validate_path(path)
        try:
            if recursive:
                await asyncio.to_thread(shutil.rmtree, path)
            else:
                await aiofiles.os.rmdir(path)
        except Exception as e:
            raise FileOperationError(f"Failed to delete directory {path}: {str(e)}")
            
    async def list_directory(self, path: Union[str, Path]) -> List[Dict[str, Any]]:
        """List directory contents with metadata."""
        path = self._validate_path(path)
        try:
            entries = []
            async for entry in aiofiles.os.scandir(path):
                stat = await aiofiles.os.stat(entry.path)
                entries.append({
                    'name': entry.name,
                    'path': str(entry.path),
                    'is_file': entry.is_file(),
                    'is_dir': entry.is_dir(),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
            return entries
        except Exception as e:
            raise FileOperationError(f"Failed to list directory {path}: {str(e)}")
            
    async def copy(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """Copy file or directory."""
        src = self._validate_path(src)
        dst = self._validate_path(dst)
        try:
            if await aiofiles.os.path.isfile(src):
                await asyncio.to_thread(shutil.copy2, src, dst)
            else:
                await asyncio.to_thread(shutil.copytree, src, dst)
        except Exception as e:
            raise FileOperationError(f"Failed to copy {src} to {dst}: {str(e)}")
            
    async def move(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """Move file or directory."""
        src = self._validate_path(src)
        dst = self._validate_path(dst)
        try:
            await asyncio.to_thread(shutil.move, src, dst)
        except Exception as e:
            raise FileOperationError(f"Failed to move {src} to {dst}: {str(e)}")
            
    async def read_json(self, path: Union[str, Path], encoding: str = 'utf-8') -> Dict[str, Any]:
        """Read and parse JSON file."""
        content = await self.read_file(path, encoding)
        try:
            return json.loads(content)
        except Exception as e:
            raise FileOperationError(f"Failed to parse JSON from {path}: {str(e)}")
            
    async def write_json(self, path: Union[str, Path], data: Dict[str, Any], 
                        indent: int = 2, encoding: str = 'utf-8') -> None:
        """Write data to JSON file."""
        try:
            content = json.dumps(data, indent=indent)
            await self.write_file(path, content, encoding)
        except Exception as e:
            raise FileOperationError(f"Failed to write JSON to {path}: {str(e)}")
            
    async def read_yaml(self, path: Union[str, Path], encoding: str = 'utf-8') -> Dict[str, Any]:
        """Read and parse YAML file."""
        content = await self.read_file(path, encoding)
        try:
            return yaml.safe_load(content)
        except Exception as e:
            raise FileOperationError(f"Failed to parse YAML from {path}: {str(e)}")
            
    async def write_yaml(self, path: Union[str, Path], data: Dict[str, Any],
                        encoding: str = 'utf-8') -> None:
        """Write data to YAML file."""
        try:
            content = yaml.dump(data, default_flow_style=False)
            await self.write_file(path, content, encoding)
        except Exception as e:
            raise FileOperationError(f"Failed to write YAML to {path}: {str(e)}")
            
    async def get_file_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Get detailed file information."""
        path = self._validate_path(path)
        try:
            stat = await aiofiles.os.stat(path)
            return {
                'path': str(path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'is_file': await aiofiles.os.path.isfile(path),
                'is_dir': await aiofiles.os.path.isdir(path),
                'is_symlink': await aiofiles.os.path.islink(path)
            }
        except Exception as e:
            raise FileOperationError(f"Failed to get file info for {path}: {str(e)}")
