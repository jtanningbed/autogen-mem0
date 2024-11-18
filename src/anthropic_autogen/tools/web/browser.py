"""
Web browser tool for navigating and interacting with web pages.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from autogen_core.base import CancellationToken
from playwright.async_api import async_playwright

from ...core.tools import BaseTool, ToolResult


class WebBrowserInput(BaseModel):
    """Input for web browser operations."""
    url: str = Field(description="URL to navigate to")
    action: str = Field(description="Action to perform (navigate, click, type, etc)")
    selector: Optional[str] = Field(None, description="CSS selector for element")
    value: Optional[str] = Field(None, description="Value to input")


class WebBrowserOutput(BaseModel):
    """Output from web browser operations."""
    success: bool = Field(description="Whether the operation was successful")
    content: Optional[str] = Field(None, description="Page content or operation result")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the operation"
    )


class WebBrowser(BaseTool):
    """Tool for web browser automation."""

    def __init__(self):
        """Initialize web browser tool."""
        super().__init__(
            name="web_browser",
            description="Tool for navigating and interacting with web pages",
            return_type=WebBrowserOutput
        )
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()

    async def execute(self, **kwargs) -> ToolResult:
        """Execute web browser operation.
        
        Args:
            url: URL to navigate to
            action: Action to perform
            selector: Optional CSS selector
            value: Optional value to input
            
        Returns:
            ToolResult: Result of the operation
        """
        try:
            input_model = WebBrowserInput(**kwargs)
            await self._ensure_browser()
            
            if input_model.action == "navigate":
                await self._page.goto(input_model.url)
                content = await self._page.content()
            elif input_model.action == "click":
                await self._page.click(input_model.selector)
                content = "Click successful"
            elif input_model.action == "type":
                await self._page.fill(input_model.selector, input_model.value)
                content = "Type successful"
            else:
                raise ValueError(f"Unknown action: {input_model.action}")

            return ToolResult(
                success=True,
                output=content,
                metadata={"url": input_model.url}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def cleanup(self):
        """Clean up browser resources."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
