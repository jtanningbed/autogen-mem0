# Anthropic AutoGen

A Python framework for building autonomous agent systems powered by Anthropic's Claude models.

## Features

- Flexible agent architecture with base classes for chat and task-based agents
- Built-in support for Claude 3 models (Opus, Sonnet, Haiku)
- Asynchronous message queue for agent communication
- Robust task management and execution
- Extensible tool system for file/shell operations
- Type-safe with full Pydantic model support
- Web-based user interface for interactive sessions
- Advanced data analysis and visualization capabilities 
- Workflow orchestration for complex multi-agent tasks

## Installation

```bash
uv pip install -e ".[test]"
```

## Quick Start

```python
from anthropic_autogen.agents.specialized.assistants import DataAnalysisAssistant
from anthropic_autogen.agents.specialized.user_interfaces import WebUIUserProxy
from anthropic_autogen.agents.specialized.orchestrators import WorkflowOrchestratorAgent

# Create specialized agents
data_analyst = DataAnalysisAssistant(agent_id="data_analyst")
web_ui = WebUIUserProxy(agent_id="web_ui", port=8000)
orchestrator = WorkflowOrchestratorAgent(agent_id="orchestrator")

# Register agents with orchestrator
orchestrator.register_agent("data_analyst", data_analyst)
orchestrator.register_agent("web_ui", web_ui)

# Start web interface
await web_ui.start()
```

## Architecture

The system is built around several core components:

- **Agents**: Base classes for different agent types (orchestrator,chat, task)
- **Tools**: Extensible system for tool and function operations
- **Task Management**: Handles task lifecycle and dependencies
- **Specialized Agents**:
  - Data Analysis Assistant: Advanced data processing and visualization
  - Web UI: Interactive web-based user interface
  - Workflow Orchestrator: Complex task coordination
- **Message Types**:
  - Chat Messages: General communication
  - Task Messages: Specific actions and operations
  - System Messages: Control and status updates

See the [architecture documentation](docs/architecture/README.md) for details.

## Development

Requirements:
- Python 3.12+
- uv package manager
- autogen-core==0.4.0.dev6
- autogen-ext==0.4.0.dev6

## License

MIT License
