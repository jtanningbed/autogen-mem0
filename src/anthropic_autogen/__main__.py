"""
Main entry point for anthropic-autogen.
"""

import asyncio
import click
from typing import Optional

from .core.orchestrator import Orchestrator
from .tools import GitHubConnector
from .agents.github_agent import GitHubAgent

@click.group()
def cli():
    """Anthropic Autogen CLI."""
    pass

@cli.command()
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub API token')
@click.option('--github-owner', envvar='GITHUB_OWNER', help='GitHub repository owner')
@click.option('--github-repo', envvar='GITHUB_REPO', help='GitHub repository name')
def interactive(
    github_token: Optional[str] = None,
    github_owner: Optional[str] = None,
    github_repo: Optional[str] = None,
):
    """Start interactive session."""
    
    async def main():
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Set up GitHub agent if credentials provided
        if all([github_token, github_owner, github_repo]):
            github = GitHubConnector(
                api_key=github_token,
                owner=github_owner,
                repo=github_repo
            )
            github_agent = GitHubAgent(github=github)
            orchestrator.add_agent(github_agent)
            
        print("Welcome to Anthropic Autogen!")
        print("Available agents:", ", ".join(orchestrator.agents.keys()))
        print("Enter 'quit' to exit")
        
        while True:
            try:
                goal = input("\nWhat would you like to do? ")
                if goal.lower() == 'quit':
                    break
                    
                if not orchestrator.agents:
                    print("No agents configured. Please provide API credentials.")
                    continue
                    
                # Use first agent as planner for simplicity
                planner = next(iter(orchestrator.agents.values()))
                responses = await orchestrator.plan_and_execute(goal, planner.name)
                
                print("\nResponses:")
                for response in responses:
                    print(f"{response.role}: {response.content}")
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                
    asyncio.run(main())

if __name__ == '__main__':
    cli()
