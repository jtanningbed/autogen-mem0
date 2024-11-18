Goal: 

Leverage autogen_core and autogen_ext to build a fully integrated personal AI assistant for day to day use. 

Desired Modularity: 

- core agent components: 
    - (autogen-core components) autogen_core.base.Agent, autogen_core.base.BaseAgent, autogen_core.components.RoutedAgent, autogen_core.base.AgentId, 
    - Create modular agents from the autogen-core components for specialized use cases (executing specific tools, running functions, planning, communicating with user, etc.)
        - chat
        - function calling, tooling 
        - user proxy 
        - task management
        - orchestration
        - computer use
        - etc... 

- core tool components:
    - (autogen-core components) autogen_core.components.tools.BaseTool, autogen_core.components.tools.FunctionTool, autogen_core.components.tools.Tool, ToolSchema, ParameterSchema, PythonCodeExecutionTool, etc.
    - (autogen-core components) autogen_core.components.tool_agent.ToolAgent, tool_agent_caller_loop(), etc.
    - Create modular tools for specialized use cases
        - file operations
        - shell commands
        - diagram generation
        - code generation
        - data visualization
        - external API calls
        - data analysis
        - database operations
        - text to speech
        - speech to text
        - image generation
        - video generation
        - audio generation
        - video editing
        - audio editing
        - etc...

- core message components: 
    - pydantic.BaseModel schemas (defined on our own, used to facilitate communication between all parties, agents, tools, etc.)
    - (autogen-core components) When used with RoutedAgent, autogen_core.components.message_handler implementation for handling message based on pydantic message class
    - (autogen-core components) autogen_core.base.MessageContext; support BroadcastMessage and Request/Response Message
    - asynchrounous messaging system (autogen implementation)

- runtime components:
    - (autogen-core components) autogen_core.base.AgentRuntime, mainly autogen_core.application.SingleThreadedAgentRuntime for local use, autogen_core.application.WorkerAgentRuntime and autogen_core.application.WorkerAgentRuntimeHost for distributed use
    
- core model components:
    - (autogen-core components) autogen_core.components.model.AssistantMessage, autogen_core.components.model.ChatCompletionClient, autogen_core.components.model.LLMMessage, autogen_core.components.model.SystemMessage, autogen_core.components.model.UserMessage, etc.
    - chat completion client in autogen uses OpenAI's chat completion api . BIG part of this project is to build integration with Anthropic API and Open Source LLMs.

- logging: 
    - use autogen logging built on python logging module, or build our own. Should be fun and visual with emojis and colors to represent different agents/tools/flows.

- configuration:
    - API keys, system prompts, etc. can be assigned to agents/tools. 
    - stateful interactions with users (chat history, task history, memory, RAG, etc.)
    - build out a memory solution where user interaction from past sessions is available to agents and tools and they learn my own behavior patterns and become closer to me over time. 
    - personalization - give the agent a name, personality, etc. 

# Desired Invocation Patterns:
- `uv run main` with arguments specifying mode, api, configurations, etc. include interactive mode.
    - begins an interactive shell session to chat with a main agent. 
    - based on input, agent can respond to user, plan a task, broadcast a message, send a direct message to another agent, start a group chat, etc.
    - downstream agents can respond, perform tasks, run functions, execute tools, give feedback, reply to user, reply to original agent, etc.

- docker to deploy a more complex predefined workflow 
- langgraph integration to define more systematic workflows
- ways to run tasks in the background

DESIGN PATTERNS: 
    - Group chat is a design pattern where a group of agents share a common thread of messages: they all subscribe and publish to the same topic. Each participant agent is specialized for a particular task, such as writer, illustrator, and editor in a collaborative writing task. You can also include an agent to represent a human user to help guide the agents when needed.

    In a group chat, participants take turn to publish a message, and the process is sequential – only one agent is working at a time. Under the hood, the order of turns is maintained by a Group Chat Manager agent, which selects the next agent to speak upon receving a message. The exact algorithm for selecting the next agent can vary based on your application requirements. Typically, a round-robin algorithm or a selector with an LLM model is used.

    Group chat is useful for dynamically decomposing a complex task into smaller ones that can be handled by specialized agents with well-defined roles. It is also possible to nest group chats into a hierarchy with each participant a recursive group chat.

    In this example, we use AutoGen’s Core API to implement the group chat pattern using event-driven agents. Please first read about Topics and Subscriptions to understand the concepts and then Messages and Communication to learn the API usage for pub-sub. We will demonstrate a simple example of a group chat with a LLM-based selector for the group chat manager, to create content for a children’s story book.

    - Handoff is a multi-agent design pattern introduced by OpenAI in an experimental project called Swarm. The key idea is to let agent delegate tasks to other agents using a special tool call.
    We can use the AutoGen Core API to implement the handoff pattern using event-driven agents. Using AutoGen (v0.4+) provides the following advantages over the OpenAI implementation and the previous version (v0.2):
    It can scale to distributed environment by using distributed agent runtime.
    It affords the flexibility of bringing your own agent implementation.
    The natively async API makes it easy to integrate with UI and other systems.
    This notebook demonstrates a simple implementation of the handoff pattern. It is recommended to read Topics and Subscriptions to understand the basic concepts of pub-sub and event-driven agents.

    - Mixture of Agents is a multi-agent design pattern that models after the feed-forward neural network architecture.
    The pattern consists of two types of agents: worker agents and a single orchestrator agent. Worker agents are organized into multiple layers, with each layer consisting of a fixed number of worker agents. Messages from the worker agents in a previous layer are concatenated and sent to all the worker agents in the next layer.
    This example implements the Mixture of Agents pattern using the core library following the original implementation of multi-layer mixture of agents.
    Here is a high-level procedure overview of the pattern:
    The orchestrator agent takes input a user task and first dispatches it to the worker agents in the first layer.
    The worker agents in the first layer process the task and return the results to the orchestrator agent.
    The orchestrator agent then synthesizes the results from the first layer and dispatches an updated task with the previous results to the worker agents in the second layer.
    The process continues until the final layer is reached.
    In the final layer, the orchestrator agent aggregates the results from previous layer and returns a single final result to the user.

    - Multi-Agent Debate is a multi-agent design pattern that simulates a multi-turn interaction where in each turn, agents exchange their responses with each other, and refine their responses based on the responses from other agents.
    This example shows an implementation of the multi-agent debate pattern for solving math problems from the GSM8K benchmark.
    There are of two types of agents in this pattern: solver agents and an aggregator agent. The solver agents are connected in a sparse manner following the technique described in Improving Multi-Agent Debate with Sparse Communication Topology. The solver agents are responsible for solving math problems and exchanging responses with each other. The aggregator agent is responsible for distributing math problems to the solver agents, waiting for their final responses, and aggregating the responses to get the final answer.
    The pattern works as follows:
    User sends a math problem to the aggregator agent.
    The aggregator agent distributes the problem to the solver agents.
    Each solver agent processes the problem, and publishes a response to its neighbors.
    Each solver agent uses the responses from its neighbors to refine its response, and publishes a new response.
    Repeat step 4 for a fixed number of rounds. In the final round, each solver agent publishes a final response.
    The aggregator agent uses majority voting to aggregate the final responses from all solver agents to get a final answer, and publishes the answer.

    - Reflection is a design pattern where an LLM generation is followed by a reflection, which in itself is another LLM generation conditioned on the output of the first one. For example, given a task to write code, the first LLM can generate a code snippet, and the second LLM can generate a critique of the code snippet.
    In the context of AutoGen and agents, reflection can be implemented as a pair of agents, where the first agent generates a message and the second agent generates a response to the message. The two agents continue to interact until they reach a stopping condition, such as a maximum number of iterations or an approval from the second agent.
    Let’s implement a simple reflection design pattern using AutoGen agents. There will be two agents: a coder agent and a reviewer agent, the coder agent will generate a code snippet, and the reviewer agent will generate a critique of the code snippet.


pyproject.toml for dependencies.
uv package manager
python==3.12
autogen-core==0.4.0.dev6
autogen-ext==0.4.0.dev6

# Implementation Plan

## 1. Project Structure

```
anthropic-autogen/
├── src/
│   └── anthropic_autogen/
│       ├── agents/
│       │   ├── base.py           # Base agent implementations
│       │   ├── chat.py           # Chat-specific agents
│       │   ├── task.py           # Task execution agents
│       │   └── orchestrator.py   # Workflow orchestration
│       ├── models/
│       │   ├── anthropic.py      # Anthropic API integration
│       │   └── open_source.py    # Open source LLM integrations
│       ├── tools/
│       │   ├── file.py           # File operations
│       │   ├── shell.py          # Shell commands
│       │   ├── media.py          # Media processing tools
│       │   └── data.py           # Data processing tools
│       ├── messaging/
│       │   ├── schemas.py        # Pydantic message schemas
│       │   └── handlers.py       # Message handling logic
│       ├── memory/
│       │   ├── store.py          # Memory storage
│       │   └── retrieval.py      # Memory retrieval logic
│       └── runtime/
│           ├── local.py          # Local runtime implementation
│           └── distributed.py     # Distributed runtime support
```

## 2. Migration Plan

### Phase 1: Core Infrastructure
1. Remove custom implementations in favor of autogen-core:
   - Replace BaseAgent with autogen_core.base.Agent
   - Remove custom MessageQueue
   - Remove custom TaskManager
   - Remove custom AgentFactory

2. Implement Anthropic Integration:
   - Create AnthropicChatCompletionClient extending autogen_core.components.model.ChatCompletionClient
   - Implement Claude-specific message handling
   - Add Claude model configuration

### Phase 3: Agent Implementation
1. Create specialized agents extending autogen_core components:
   - OrchestratorAgent: Task planning and delegation
   - UserProxyAgent: User interaction handling
   - ToolAgent: Tool execution wrapper
   - ComputeAgent: System operations

2. Implement group chat patterns:
   - GroupChatManager using autogen message routing
   - Turn management logic
   - Dynamic agent selection

### Phase 4: Tool Development
1. Implement core tools using autogen_core.components.tools:
   - FileOperationTool
   - ShellCommandTool
   - DiagramGenerationTool
   - APIIntegrationTool

2. Add media processing tools:
   - TextToSpeechTool
   - SpeechToTextTool
   - ImageGenerationTool
   - VideoProcessingTool

### Phase 5: Memory System
1. Implement persistent storage:
   - Chat history
   - Task history
   - User preferences
   - Agent state

2. Add retrieval mechanisms:
   - Context-aware search
   - Pattern recognition
   - Behavioral learning

### Phase 6: Runtime and Configuration
1. Setup runtime environments:
   - SingleThreadedAgentRuntime for local use
   - WorkerAgentRuntime for distributed scenarios

2. Implement configuration management:
   - API key handling
   - System prompt management
   - Agent personality configuration
   - Tool settings

## 3. Testing Strategy

1. Unit Tests:
   - Agent behavior
   - Tool functionality
   - Message handling
   - Memory operations

2. Integration Tests:
   - Multi-agent workflows
   - Group chat scenarios
   - Tool chaining
   - Memory persistence

3. System Tests:
   - End-to-end workflows
   - Performance benchmarks
   - Reliability testing

## 4. Deployment Strategy

1. Local Development:
   - `uv run main` with interactive mode
   - Configuration via environment variables
   - Local file system storage

2. Containerized Deployment:
   - Docker compose setup
   - Volume mounting for persistence
   - Environment configuration

3. Distributed Setup:
   - WorkerAgentRuntime configuration
   - Message queue integration
   - Shared storage solution

## Next Steps

1. Begin Phase 1 implementation:
   - Setup project structure
   - Remove custom implementations
   - Integrate autogen-core base components

2. Start Anthropic integration:
   - Implement ChatCompletionClient
   - Test with Claude models
   - Document API patterns

3. Setup development environment:
   - Configure uv package manager
   - Setup testing framework
   - Initialize Docker environment
