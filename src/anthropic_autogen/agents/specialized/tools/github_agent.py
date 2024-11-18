"""
GitHub agent implementation.
Specializes in GitHub operations and repository management.
"""

from typing import List, Optional
from ..core.agent import BaseAgent, Message
from ..tools import GitHubConnector
from ....agents.base.tool_agent import BaseToolAgent

class GitHubAgent(BaseToolAgent):
    """Agent for interacting with GitHub."""
    
    def __init__(
        self,
        github: GitHubConnector,
        name: str = "github_agent",
        description: str = "Agent for GitHub operations",
    ):
        """Initialize GitHub agent.
        
        Args:
            github: GitHub connector instance
            name: Agent name
            description: Agent description
        """
        super().__init__(name=name, description=description, tools=[github])
        self.github = github
        
    async def process_message(self, message: Message) -> Message:
        """Process GitHub-related request.
        
        Args:
            message: Request message
            
        Returns:
            Response message
        """
        # Simple example: list issues when asked
        if "list issues" in message.content.lower():
            issues = await self.github.list_issues()
            response = "Found issues:\n"
            for issue in issues:
                response += f"- #{issue.number}: {issue.title} ({issue.state})\n"
            return Message(role="assistant", content=response)
            
        return Message(
            role="assistant",
            content="I can help with GitHub operations. Try asking me to list issues."
        )
        
    async def plan(self, goal: str) -> List[str]:
        """Plan GitHub operations.
        
        Args:
            goal: Goal to achieve
            
        Returns:
            List of planned steps
        """
        # Simple example: always delegates to self
        return [f"{self.name}: {goal}"]
        
    async def execute_step(self, step: str) -> Message:
        """Execute GitHub operation.
        
        Args:
            step: Operation to execute
            
        Returns:
            Result message
        """
        return await self.process_message(Message(role="user", content=step))
