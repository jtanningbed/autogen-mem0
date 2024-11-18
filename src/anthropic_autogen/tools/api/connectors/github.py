"""
GitHub API connector.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ..base import BaseAPIConnector, APIResponse

class GitHubIssue(BaseModel):
    """GitHub issue model."""
    number: int
    title: str
    state: str
    body: Optional[str]
    labels: List[str]
    assignees: List[str]
    created_at: str
    updated_at: str

class GitHubConnector(BaseAPIConnector):
    """GitHub API connector."""
    
    def __init__(
        self,
        api_key: str,
        owner: str,
        repo: str,
        timeout: int = 30,
    ):
        """Initialize GitHub connector.
        
        Args:
            api_key: GitHub API token
            owner: Repository owner
            repo: Repository name
            timeout: Request timeout in seconds
        """
        super().__init__(
            base_url="https://api.github.com",
            api_key=api_key,
            timeout=timeout,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )
        self.owner = owner
        self.repo = repo
        
    async def validate_credentials(self) -> bool:
        """Validate GitHub credentials."""
        try:
            response = await self.get("/user")
            return response.status_code == 200
        except Exception:
            return False
            
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get GitHub API rate limits."""
        response = await self.get("/rate_limit")
        return response.data
        
    async def list_issues(
        self,
        state: str = "open",
        labels: Optional[List[str]] = None,
        since: Optional[str] = None,
    ) -> List[GitHubIssue]:
        """List repository issues.
        
        Args:
            state: Issue state (open, closed, all)
            labels: Filter by labels
            since: ISO 8601 timestamp
            
        Returns:
            List of GitHubIssue objects
        """
        params = {
            "state": state,
            "per_page": 100,
        }
        if labels:
            params["labels"] = ",".join(labels)
        if since:
            params["since"] = since
            
        response = await self.get(
            f"/repos/{self.owner}/{self.repo}/issues",
            params=params
        )
        
        return [GitHubIssue(**issue) for issue in response.data]
        
    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> GitHubIssue:
        """Create a new issue.
        
        Args:
            title: Issue title
            body: Issue body
            labels: Issue labels
            assignees: Issue assignees
            
        Returns:
            Created GitHubIssue object
        """
        data = {
            "title": title,
            "body": body,
        }
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
            
        response = await self.post(
            f"/repos/{self.owner}/{self.repo}/issues",
            data=data
        )
        
        return GitHubIssue(**response.data)
        
    async def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> GitHubIssue:
        """Update an existing issue.
        
        Args:
            issue_number: Issue number
            title: New title
            body: New body
            state: New state
            labels: New labels
            assignees: New assignees
            
        Returns:
            Updated GitHubIssue object
        """
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels
        if assignees is not None:
            data["assignees"] = assignees
            
        response = await self.patch(
            f"/repos/{self.owner}/{self.repo}/issues/{issue_number}",
            data=data
        )
        
        return GitHubIssue(**response.data)
