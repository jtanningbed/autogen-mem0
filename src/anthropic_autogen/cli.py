import click
import asyncio
import yaml
from pathlib import Path
from .workflow import WorkflowManager
from .config import Config
from .tools import ShellTool

@click.group()
def cli():
    """Anthropic Autogen CLI"""
    pass

@cli.command()
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
def chat(config, api_key):
    """Start interactive chat session"""
    async def run():
        # Load config
        cfg = Config()
        if config:
            with open(config) as f:
                cfg = Config.model_validate(yaml.safe_load(f))

        if api_key:
            cfg.api_key = api_key

        if not cfg.api_key:
            raise click.ClickException("API key required")

        # Create workflow manager
        manager = WorkflowManager(
            api_key=cfg.api_key, model=cfg.default_model, tools=[ShellTool()]
        )

        await manager.start()

        # Interactive loop
        try:
            while True:
                msg = click.prompt('You')
                if msg.lower() in ('exit', 'quit'):
                    break

                response = await manager.chat(msg)
                click.echo(f'Claude: {response}')

        finally:
            await manager.stop()

    asyncio.run(run())

if __name__ == '__main__':
    cli()
