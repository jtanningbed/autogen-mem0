# Anthropic AutoGen

A Python framework for building autonomous agent systems powered by Anthropic's Claude models.

## Features

- Flexible agent architecture with base classes for chat and task-based agents
- Built-in support for Claude 3 models (Opus, Sonnet, Haiku)
- Asynchronous message queue for agent communication
- Robust task management and execution
- Extensible tool system for file/shell operations
- Type-safe with full Pydantic model support

## Installation

```bash
pip install anthropic-autogen
```

## Quick Start

```python
from anthropic_autogen import AnthropicChatCompletionClient, ChatAgent

# Initialize the Claude client
client = AnthropicChatCompletionClient(
    model="claude-3-opus-20240229",
    api_key="your-api-key"
)

# Create a chat agent
agent = ChatAgent(
    agent_id="chat-agent-1",
    name="Assistant",
    client=client
)

# Start conversation
await agent.start()
```

## Architecture

The system is built around several core components:

- **Agents**: Base classes for different agent types (chat, task)
- **Tools**: Extensible system for file/shell operations
- **Messaging**: Async queue for agent communication
- **Task Management**: Handles task lifecycle and dependencies

See the [architecture documentation](docs/architecture/README.md) for details.

## Development

Requirements:
- Python 3.12+
- anthropic>=0.39.0
- autogen-core==0.4.0.dev6
- autogen-ext==0.4.0.dev6

## License

MIT License
