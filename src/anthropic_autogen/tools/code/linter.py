"""
Code linting tool implementation.
"""

import pylint.lint
from pylint.reporters import JSONReporter
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import asyncio
import logging
import io
import json
from dataclasses import dataclass, asdict
from pydantic import BaseModel

from ...core.tools import BaseTool, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class LintMessage:
    """Represents a single lint message."""
    msg_id: str
    symbol: str
    msg: str
    line: int
    column: int
    path: str
    module: str
    obj: str
    category: str
    confidence: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class JSONReporterWithMessages(JSONReporter):
    """Custom JSON reporter that captures messages during linting."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages = []
        self._output = io.StringIO()
    
    def handle_message(self, msg):
        """Handle a lint message."""
        self._messages.append(msg)
        super().handle_message(msg)
    
    @property
    def messages(self):
        """Get all captured messages."""
        return self._messages


class LintResult(BaseModel):
    """Result of a lint operation."""
    messages: List[Dict[str, Any]]
    stats: Dict[str, Any]


class Linter(BaseTool):
    """Tool for linting Python code using pylint."""
    
    def __init__(
            self,
            name: str,
            description: str,
            return_type: type[BaseModel],
            config_file: Optional[Union[str, Path]] = None,
            ignore_patterns: Optional[List[str]] = None,
            **kwargs
        ):
        """Initialize linter.
        
        Args:
            name: Tool name
            description: Tool description
            return_type: Return type class
            config_file: Optional path to pylint config file
            ignore_patterns: Optional list of patterns to ignore
            **kwargs: Additional configuration
        """
        super().__init__(name=name, description=description, return_type=return_type)
        self.config_file = Path(config_file) if config_file else None
        self.ignore_patterns = ignore_patterns or []
    
    def _parse_message(self, msg) -> LintMessage:
        """Parse a pylint message into a LintMessage object."""
        return LintMessage(
            msg_id=msg.msg_id,
            symbol=msg.symbol,
            msg=msg.msg,
            line=msg.line,
            column=msg.column,
            path=str(msg.path),
            module=msg.module,
            obj=msg.obj,
            category=msg.category,
            confidence=msg.confidence.name
        )
    
    async def execute(
            self,
            target: Union[str, Path],
            disable: Optional[List[str]] = None,
            enable: Optional[List[str]] = None,
            jobs: int = 1,
            recursive: bool = True,
            **kwargs
        ) -> ToolResult:
        """Lint Python code.
        
        Args:
            target: File or directory to lint
            disable: List of messages to disable
            enable: List of messages to enable
            jobs: Number of parallel jobs
            recursive: Whether to lint recursively
            **kwargs: Additional pylint arguments
            
        Returns:
            ToolResult: Linting result with:
                - success: Whether linting completed without errors
                - output: List of lint messages
                - error: Error message if linting failed
                - metadata: Detailed lint statistics
        """
        try:
            target_path = Path(target)
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    output=[],
                    error=f"Target path does not exist: {target_path}"
                )
            
            reporter = JSONReporterWithMessages()
            args = ["--output-format=json"]
            
            if self.config_file:
                args.extend(["--rcfile", str(self.config_file)])
            
            if disable:
                args.extend(["--disable", ",".join(disable)])
            if enable:
                args.extend(["--enable", ",".join(enable)])
            
            if jobs > 1:
                args.extend(["--jobs", str(jobs)])
            
            if recursive and target_path.is_dir():
                args.extend(["--recursive", "y"])
            
            args.extend(kwargs.get("args", []))
            args.append(str(target_path))
            
            # Run pylint
            pylint.lint.Run(args, reporter=reporter, exit=False)
            
            # Parse messages
            messages = [
                self._parse_message(msg).to_dict()
                for msg in reporter.messages
            ]
            
            # Get statistics
            stats = json.loads(reporter._output.getvalue())
            
            result = LintResult(
                messages=messages,
                stats=stats
            )
            
            return ToolResult(
                success=True,
                output=result.model_dump(),
                metadata={"stats": stats}
            )
            
        except Exception as e:
            logger.exception("Linting failed")
            return ToolResult(
                success=False,
                output=[],
                error=str(e)
            )
