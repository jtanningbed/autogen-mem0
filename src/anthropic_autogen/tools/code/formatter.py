"""
Code formatting tool implementation.
"""

import black
import isort
from pathlib import Path
from typing import List, Optional, Union
import asyncio
import logging

from ...core.tools import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class CodeFormatter(BaseTool):
    """Tool for formatting code using black and isort."""

    @property
    def name(self) -> str:
        return "code_formatter"

    @property
    def description(self) -> str:
        return "Formats Python code using black for code style and isort for import sorting"

    async def execute(
        self,
        target: Union[str, Path],
        line_length: int = 88,
        skip_string_normalization: bool = False,
        **kwargs
    ) -> ToolResult:
        """Format Python code.
        
        Args:
            target: File or directory to format
            line_length: Maximum line length
            skip_string_normalization: Skip string normalization
            **kwargs: Additional arguments passed to black/isort
            
        Returns:
            ToolResult: Formatting result with:
                - success: Whether formatting was successful
                - output: List of formatted files
                - error: Error message if formatting failed
        """
        try:
            target_path = Path(target)
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    output=[],
                    error=f"Target path does not exist: {target}"
                )

            # Collect Python files
            if target_path.is_file():
                if not target_path.suffix == '.py':
                    return ToolResult(
                        success=False,
                        output=[],
                        error=f"Not a Python file: {target}"
                    )
                files = [target_path]
            else:
                files = list(target_path.rglob('*.py'))

            if not files:
                return ToolResult(
                    success=True,
                    output=[],
                    metadata={"message": "No Python files found"}
                )

            formatted_files = []
            errors = []

            # Format files
            for file_path in files:
                try:
                    # Read file content
                    content = file_path.read_text()

                    # Format with black
                    mode = black.FileMode(
                        line_length=line_length,
                        string_normalization=not skip_string_normalization
                    )
                    formatted = black.format_str(content, mode=mode)

                    # Sort imports with isort
                    sorted_imports = isort.code(
                        formatted,
                        line_length=line_length,
                        profile="black"
                    )

                    # Write back if changed
                    if sorted_imports != content:
                        file_path.write_text(sorted_imports)
                        formatted_files.append(str(file_path))

                except Exception as e:
                    errors.append(f"Error formatting {file_path}: {str(e)}")
                    logger.error(f"Formatting error in {file_path}", exc_info=True)

            if errors:
                return ToolResult(
                    success=False,
                    output=formatted_files,
                    error="\n".join(errors)
                )

            return ToolResult(
                success=True,
                output=formatted_files,
                metadata={
                    "files_processed": len(files),
                    "files_modified": len(formatted_files)
                }
            )

        except Exception as e:
            logger.error("Formatting failed", exc_info=True)
            return ToolResult(
                success=False,
                output=[],
                error=f"Formatting failed: {str(e)}"
            )
