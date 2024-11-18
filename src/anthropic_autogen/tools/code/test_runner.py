"""
Test runner tool implementation.
"""

import pytest
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import asyncio
import logging
from _pytest.main import Session
from _pytest.reports import TestReport
from _pytest.nodes import Item
from pydantic import BaseModel

from ...core.tools import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class TestResultCollector:
    """Collects test results during pytest execution."""

    def __init__(self):
        self.results = []
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "xfailed": 0,
            "xpassed": 0
        }
    
    def pytest_runtest_logreport(self, report: TestReport):
        """Collect test results."""
        if report.when == "call":
            self.results.append({
                "nodeid": report.nodeid,
                "outcome": report.outcome,
                "longrepr": str(report.longrepr) if report.longrepr else None,
                "sections": [
                    {"title": title, "content": content}
                    for title, content, _ in (report.sections or [])
                ],
                "duration": report.duration
            })
            
            self.summary["total"] += 1
            if report.passed:
                if hasattr(report, "wasxfail"):
                    self.summary["xpassed"] += 1
                else:
                    self.summary["passed"] += 1
            elif report.failed:
                if hasattr(report, "wasxfail"):
                    self.summary["xfailed"] += 1
                else:
                    self.summary["failed"] += 1
            elif report.skipped:
                self.summary["skipped"] += 1


class TestResult(BaseModel):
    """Result of a test run."""
    results: List[Dict[str, Any]]
    summary: Dict[str, int]


class TestRunner(BaseTool):
    """Tool for running Python tests using pytest."""
    
    def __init__(
            self,
            name: str,
            description: str,
            return_type: type[BaseModel],
            **kwargs
        ):
        """Initialize test runner.
        
        Args:
            name: Tool name
            description: Tool description
            return_type: Return type class
            **kwargs: Additional configuration
        """
        super().__init__(name=name, description=description, return_type=return_type)
    
    async def execute(
            self,
            target: Union[str, Path],
            pattern: str = "test_*.py",
            markers: Optional[List[str]] = None,
            verbose: bool = True,
            capture_output: bool = True,
            fail_fast: bool = False,
            **kwargs
        ) -> ToolResult:
        """Run Python tests.
        
        Args:
            target: Directory or file containing tests
            pattern: Test file pattern to match
            markers: Optional list of pytest markers to select
            verbose: Whether to use verbose output
            capture_output: Whether to capture stdout/stderr
            fail_fast: Stop on first failure
            **kwargs: Additional pytest arguments
            
        Returns:
            ToolResult: Test execution result with:
                - success: Whether all tests passed
                - output: Test execution summary
                - error: Error message if execution failed
                - metadata: Detailed test statistics
        """
        try:
            target_path = Path(target)
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    output=[],
                    error=f"Target path does not exist: {target_path}"
                )
            
            collector = TestResultCollector()
            args = []
            
            if verbose:
                args.append("-v")
            
            if not capture_output:
                args.append("-s")
            
            if fail_fast:
                args.append("-x")
            
            if markers:
                args.extend([f"-m {m}" for m in markers])
            
            if target_path.is_file():
                args.append(str(target_path))
            else:
                args.extend([
                    str(p) for p in target_path.rglob(pattern)
                ])
            
            args.extend(kwargs.get("args", []))
            
            # Run pytest
            pytest.main(args, plugins=[collector])
            
            result = TestResult(
                results=collector.results,
                summary=collector.summary
            )
            
            return ToolResult(
                success=collector.summary["failed"] == 0,
                output=result.model_dump(),
                metadata={"summary": collector.summary}
            )
            
        except Exception as e:
            logger.exception("Test execution failed")
            return ToolResult(
                success=False,
                output=[],
                error=str(e)
            )
