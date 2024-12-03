# autogen-mem0

A Python framework that extends Microsoft's AutoGen v0.4 with memory capabilities using mem0.

## Features

### Core Functionality
- **Memory Integration**: Seamless integration with mem0 for persistent memory
- **Message Adaptation**: Clean adapter pattern for message conversions
- **Configuration Management**: Robust configuration system
- **Tool-Based Memory**: Memory operations through LLM-accessible tools

### Key Components

#### Memory Enhancement
- Memory initialization and configuration at agent level
- Memory operations through dedicated tools
- Context-aware memory storage and retrieval

#### Agents
- **MemoryEnabledAssistant**: Production-ready memory-capable agent
- Tool-based memory operations
- Automatic context enhancement

#### Message System
- Clear adapter pattern for message conversion
- Support for multiple message formats
- Type-safe message handling

## Installation

```bash
uv pip install -e ".[test]"
```

## Quick Start

```python
from autogen_mem0.core.agents import MemoryEnabledAssistant
from autogen_mem0.core.config import AgentConfig
from autogen_core.components.models import ChatCompletionClient

# Configure the assistant
config = AgentConfig(
    name="memory_assistant",
    description="Memory-enabled AI assistant",
    memory_config={
        "provider": "mem0",
        "config": {
            "collection": "conversations"
        }
    }
)

# Create the assistant
assistant = MemoryEnabledAssistant(
    config=config,
    model_client=ChatCompletionClient(...),  # Your LLM configuration
)

# The assistant will use memory tools automatically
await assistant.on_messages([
    "Remember that my favorite color is blue"
])

# Later, the assistant can recall this information
await assistant.on_messages([
    "What's my favorite color?"
])
```

## Architecture

The system is built around these core components:

1. **Agents**
   - Memory initialization
   - Tool registration
   - Message processing

2. **Memory Tools**
   - Store information
   - Recall information
   - Context management

3. **Message Adapters**
   - Format conversion
   - Type safety
   - Provider compatibility

For detailed architecture information, see the [architecture documentation](docs/architecture/README.md).

## Development

Requirements:
- Python 3.12+
- uv package manager
- Microsoft AutoGen v0.4 (autogen-core==0.4.0.dev6, autogen-ext==0.4.0.dev6)
- mem0 memory backend

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests with `pytest`
4. Submit a pull request

## License

MIT License