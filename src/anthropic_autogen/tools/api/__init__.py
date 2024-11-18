"""
API tools for anthropic-autogen.
"""

from .base import BaseAPIConnector, APIResponse
from .connectors.github import GitHubConnector
# from .connectors.slack import SlackConnector
# from .connectors.jira import JiraConnector

__all__ = [
    'BaseAPIConnector',
    'APIResponse',
    'GitHubConnector',
    # 'SlackConnector', 
    # 'JiraConnector',
]
