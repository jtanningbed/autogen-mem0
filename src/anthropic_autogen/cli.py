"""
Command-line interface for the anthropic-autogen framework.
"""

import click
import asyncio
import yaml
from pathlib import Path
import logging
from typing import Optional, Dict, Any

from .core import (
    Runtime,
    Orchestrator,
    ChatMessage,
    TaskMessage,
    TaskStatus
)


@click.group()
def cli():
    """Anthropic Autogen CLI"""
    pass


@cli.command()
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.option('--model', help='Model to use for agents')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def run(config: Optional[str], model: Optional[str], verbose: bool):
    """Run an agent workflow"""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    async def execute():
        # Load config if provided
        cfg: Dict[str, Any] = {}
        if config:
            with open(config) as f:
                cfg = yaml.safe_load(f)
        
        # Create orchestrator
        orchestrator = Orchestrator(**cfg)
        
        try:
            # Example workflow using context manager
            async with orchestrator.workflow() as workflow_id:
                # Register agents
                # await orchestrator.register_agent(...)
                
                # Delegate tasks
                # task_id = await orchestrator.delegate(...)
                
                # Monitor task status
                # status = await orchestrator.get_task_status(task_id)
                pass
                
        finally:
            await orchestrator.cleanup()
    
    asyncio.run(execute())


@cli.command()
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.option('--model', help='Model to use for chat')
def chat(config: Optional[str], model: Optional[str]):
    """Start an interactive chat session"""
    
    async def execute():
        # Load config if provided
        cfg: Dict[str, Any] = {}
        if config:
            with open(config) as f:
                cfg = yaml.safe_load(f)
        
        # Create runtime
        runtime = Runtime(**cfg)
        
        try:
            # Interactive chat loop
            while True:
                # Get user input
                user_input = click.prompt('You')
                if user_input.lower() in ('exit', 'quit'):
                    break
                
                # Create chat message
                message = ChatMessage(
                    sender="user",
                    recipient="assistant",
                    content=user_input
                )
                
                # Send message and get response
                # await runtime.send_message(message)
                # response = await runtime.get_response()
                # click.echo(f'Assistant: {response.content}')
                
        finally:
            await runtime.cleanup()
    
    asyncio.run(execute())


if __name__ == '__main__':
    cli()
