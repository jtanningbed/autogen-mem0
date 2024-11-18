"""
Code assistant agent implementation.
Specializes in code generation, review, and refactoring tasks.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from ....core.agents import BaseToolAgent
from ....core.messaging import ChatMessage, TaskMessage, SystemMessage, MessageCommon as Message
from ....tools.code import (
    TestRunner,
    Linter,
    GitOperations,
    DependencyManager
)


class CodeAssistantAgent(BaseToolAgent):
    """
    Specialized agent for code-related tasks.
    Provides capabilities for code generation, review, refactoring,
    testing, and dependency management.
    """
    
    def __init__(
            self,
            agent_id: str,
            name: str = "code_assistant",
            description: str = "AI code assistant that helps with coding tasks",
            system_prompt: Optional[str] = None,
            **kwargs
        ):
        """Initialize code assistant.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            description: Agent description 
            system_prompt: Optional system prompt
            **kwargs: Additional configuration
        """
        tools = [
            TestRunner(
                name="test_runner",
                description="Run Python tests using pytest",
                return_type=BaseModel
            ),
            Linter(
                name="linter",
                description="Run code linting and style checks",
                return_type=BaseModel
            ),
            GitOperations(
                name="git",
                description="Perform Git operations",
                return_type=BaseModel
            ),
            DependencyManager(
                name="dependencies",
                description="Manage Python package dependencies",
                return_type=BaseModel
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            tools=tools,
            system_prompt=system_prompt or self._default_system_prompt(),
            **kwargs
        )
    
    def _default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are an expert code assistant that helps users with coding tasks.
        You can help with:
        - Code generation and implementation
        - Code review and feedback
        - Refactoring and optimization
        - Testing and debugging
        - Dependency management
        
        When helping users:
        1. Break down complex tasks into smaller steps
        2. Explain your thought process clearly
        3. Follow coding best practices
        4. Consider edge cases and error handling
        5. Write clear documentation and comments
        """
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming message and generate response.
        
        Args:
            message: Incoming message
            
        Returns:
            Response message
        """
        # Use LLM to process message and generate response
        response = await self.llm.generate_response(message)
        return ChatMessage(content=response)
    
    async def plan(self, goal: str) -> List[str]:
        """Plan steps to achieve goal.
        
        Args:
            goal: Goal to achieve
            
        Returns:
            List of planned steps
        """
        # Use LLM to break down goal into steps
        steps = await self.llm.generate_plan(goal)
        return steps
    
    async def execute_step(self, step: str) -> Message:
        """Execute a single step.
        
        Args:
            step: Step to execute
            
        Returns:
            Result message
        """
        # Use LLM to execute step and generate result
        result = await self.llm.execute_step(step)
        return ChatMessage(content=result)
