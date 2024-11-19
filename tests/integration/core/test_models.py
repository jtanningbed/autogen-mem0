"""Test models for agent tests."""

from pydantic import BaseModel

from anthropic_autogen.core.messaging import ChatMessage
from anthropic_autogen.core.tools import BaseTool
from autogen_core.base import CancellationToken


class GroupChatMessage(ChatMessage):
    """Test group chat message."""
    content: str
    sender: str


class TestResult(BaseModel):
    """Test result model."""
    success: bool
    message: str


class TestToolArgs(BaseModel):
    """Test tool args model."""
    pass


class TestTool(BaseTool):
    """Test tool implementation."""
    
    def __init__(self):
        """Initialize test tool."""
        super().__init__(
            name="test_tool",
            description="Test tool",
            args_schema=TestToolArgs,
            return_type=TestResult
        )
        
    async def execute(self, **args) -> dict:
        """Execute tool."""
        return {
            "success": True,
            "message": "Test tool executed"
        }

    async def run(self, args: TestToolArgs, token: CancellationToken) -> TestResult:
        """Run tool through autogen interface."""
        result = await self.execute(**args.dict())
        return TestResult(**result)
