"""Base interfaces for extending autogen agent types."""

from typing import Any, Dict, List, Optional, Type, Awaitable, Sequence
from pydantic import BaseModel, Field
import json
import logging

from autogen_core.base import CancellationToken
from autogen_core.components import RoutedAgent
from autogen_core.components.models import (
    ChatCompletionClient,
)
from autogen_core.components.models import FunctionExecutionResult
from autogen_core.components.tools import Tool
from autogen_agentchat.base import Response
from autogen_agentchat.agents import BaseChatAgent, AssistantAgent, Handoff
from autogen_agentchat.messages import (
    ChatMessage as AutogenChatMessage,
    TextMessage as AutogenTextMessage,
    HandoffMessage as AutogenHandoffMessage,
    StopMessage as AutogenStopMessage,
    MultiModalMessage as AutogenMultiModalMessage,
    ToolCallMessage as AutogenToolCallMessage,
    ToolCallResultMessage as AutogenToolCallResultMessage,
    AgentMessage as AutogenAgentMessage
)

from mem0.configs.base import MemoryConfig

from ..messaging import ( Message, AssistantMessage, UserMessage, SystemMessage, AgentMessage, ToolCallMessage, ToolCallResultMessage, HandoffMessage, StopMessage, ChatMessage, TextMessage, MultiModalMessage )
from ..memory.manager import MemoryManager
from ..config import ConfigManager
from ..tools import (
    # Memory Tools
    StoreMemoryTool,
    RecallMemoryTool
)

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Base configuration for all agents."""
    name: str = Field(description="Name of the agent")
    description: str = Field(description="Description of the agent's purpose and capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the agent")
    memory_config: Optional[MemoryConfig] = Field(default=None, description="Optional memory configuration for the agent")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context for memory operations")

    class Config:
        arbitrary_types_allowed = True

class EventAgent(RoutedAgent):
    """Base agent for event-driven functionality."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(description=config.description)
        self._config = config
        self._state: Dict[str, Any] = {}
        self._event_handlers: Dict[Type, List[Awaitable]] = {}

    @property
    def config(self) -> AgentConfig:
        """Get agent configuration."""
        return self._config

class MessageAdapter:
    """Adapter for converting between our message types and autogen message types."""
    
    @staticmethod
    def to_agent_message(msg: Message) -> AutogenAgentMessage:
        """Convert our message type to autogen AgentMessage."""
        return msg.to_autogen_message()
    
    @staticmethod
    def from_agent_message(msg: AutogenAgentMessage) -> Message:
        """Convert autogen AgentMessage to our message type."""
        if isinstance(msg, AutogenTextMessage):
            if msg.source == "system":
                return SystemMessage(content=msg.content)
            elif msg.source == "assistant":
                return AssistantMessage(content=msg.content)
            else:
                return UserMessage(content=msg.content)
                
        elif isinstance(msg, AutogenMultiModalMessage):
            return UserMessage(content=str(msg.content))
            
        elif isinstance(msg, AutogenHandoffMessage):
            return HandoffMessage(
                content=msg.content,
                target=msg.target,
                source=msg.source
            )
            
        elif isinstance(msg, AutogenStopMessage):
            return StopMessage(content=msg.content)
            
        elif isinstance(msg, AutogenToolCallMessage):
            return ToolCallMessage(
                content=msg.content,
                source=msg.source,
                tool_name=msg.content[0].name if msg.content else "",
                tool_input=msg.content[0].arguments if msg.content else {}
            )
            
        elif isinstance(msg, AutogenToolCallResultMessage):
            return ToolCallResultMessage(
                content=msg.content,
                source=msg.source,
                results=[FunctionExecutionResult(content=result.content, call_id=result.call_id) 
                        for result in msg.content]
            )
            
        else:
            # Default to UserMessage for unknown types
            return UserMessage(content=str(msg.content))

class BaseMemoryAgent(BaseChatAgent):
    """Base agent with integrated memory capabilities."""

    async def __init__(self, config: AgentConfig):
        await super().__init__(name=config.name, description=config.description)
        self._config = config
        self._memory_manager = MemoryManager(ConfigManager())
        self._memory = await self._memory_manager.get_memory(self.name, config.memory_config)
        self._model_client: Optional[ChatCompletionClient] = None

    @property
    def produced_message_types(self) -> List[Type[AutogenChatMessage]]:
        """Types of messages this agent can produce."""
        return [AutogenTextMessage, AutogenMultiModalMessage]

    async def store(
        self, 
        content: Any, 
        metadata: Optional[Dict] = None,
    ) -> None:
        """Store content in memory."""
        if self._memory:
            await self._memory.add(
                messages=content,
                metadata=metadata,
                user_id=self.name,
                filters={"user_id": self.name}
            )

    async def recall(
        self, 
        query: str,
        limit: int = 5
    ) -> List[Any]:
        """Recall content from memory."""
        if self._memory:
            return await self._memory.search(
                query=query,
                user_id=self.name,
                filters={"user_id": self.name},
                limit=limit
            )
        return []

    async def on_messages(
        self,
        messages: Sequence[AutogenChatMessage],
        cancellation_token: CancellationToken
    ) -> Response:
        """Handle incoming messages with memory integration."""
        if not messages:
            return Response(chat_message=AutogenTextMessage(content="No messages received", source=self.name))

        # Convert autogen messages to our types
        our_messages = [MessageAdapter.from_agent_message(msg) for msg in messages]

        # Add system message if not present
        if not any(isinstance(m, SystemMessage) for m in our_messages):
            if isinstance(self._system_messages, str):
                system_msg = SystemMessage(content=self._system_messages, source=self.name)
                our_messages.insert(0, system_msg)
            else:
                # Handle case where system messages might be a list or other type
                system_content = str(self._system_messages)
                system_msg = SystemMessage(content=system_content, source=self.name)
                our_messages.insert(0, system_msg)

        # Process with model client
        result = await self._model_client.create(
            messages=our_messages,
            tools=self._tools,
            cancellation_token=cancellation_token
        )
        
        # Add assistant message to model context 
        assistant_msg = AssistantMessage(
            content=result.content,
            source=self.name
        )
        self._model_context.append(assistant_msg)
        
        # Let base class handle conversion to TextMessage
        return Response(chat_message=assistant_msg)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """Reset agent state."""
        if self._memory:
            MemoryManager.clear_memory(self.name)

class MemoryEnabledAssistant(AssistantAgent):
    """Assistant agent with integrated memory capabilities."""

    def __init__(
        self,
        config: AgentConfig,
        model_client: ChatCompletionClient,
        tools: Optional[List[Tool]] = None,
        handoffs: Optional[List[Handoff | str]] = None,
        system_message: str = None
    ):
        # Initialize memory and conversation tracking
        self._config = config
        self._memory = None
        self._memory_manager = None
        self._conversation_id = None
        self._tools = tools or []  # Store tools as instance variable
        self._closed = False

        if config.memory_config:
            print("DEBUG: Initializing memory configuration")
            # Initialize memory through manager
            self._memory_manager = MemoryManager(ConfigManager())

            # Start conversation
            self._conversation_id = self._memory_manager.start_conversation()
            print(f"DEBUG: Started conversation {self._conversation_id}")

            # Initialize memory instance asynchronously
            # Note: We can't use await in __init__, so we'll initialize in an async method
            self._memory_config = config.memory_config
            self._agent_name = config.name

            # Get context from config
            context = config.context or {
                "user_id": None,
                "agent_id": config.name,
                "session_id": self._conversation_id,
                "metadata": config.metadata
            }
            context_str = json.dumps(context, indent=2)

            # Enhance system message with context
            base_system_message = system_message or """You are a helpful AI assistant with advanced memory capabilities.

1. Memory Operations:
   - Store memories with rich contextual information
   - Recall information using context-enhanced search
   - Create and maintain relationship graphs

You should:
- Use memory tools to store and retrieve information
- Think like a human would about maintaining conversation flow
- Use context from memory to enhance your responses

Example Interaction:
User: "My sister Sarah loves the cafe on Main Street"
Action: Store this information in memory with appropriate context
Action: Create graph relationships to track these connections

User: "What does she like to order there?"
Action: Use memory search to find relevant information about Sarah and the cafe
Action: Provide a natural response based on recalled information

Always strive to maintain natural conversation flow while managing memory operations behind the scenes."""

            # Add context information to system message
            system_message = f"""{base_system_message}

When using memory tools (store_memory, recall_memory), use the following context values:

{context_str}

These context values are fixed for the duration of our conversation and should be used with memory operations."""

        # async def initialize_memory(self):
        """Initialize memory instance asynchronously."""
        if self._memory_config:

            print(f"DEBUG: Initializing memory for agent {self._agent_name}")
            self._memory = self._memory_manager.get_memory(self._agent_name, memory_config=self._memory_config)
            self._tools.append(StoreMemoryTool(self._memory))
            self._tools.append(RecallMemoryTool(self._memory))
            print("DEBUG: Memory initialized")

        # Initialize AssistantAgent
        super().__init__(
            name=config.name,
            model_client=model_client,
            description=config.description,
            tools=self._tools,
            handoffs=handoffs,
            system_message=system_message,
        )

    def close(self):
        """Close memory manager and cleanup resources."""
        if self._closed:
            return
            
        logger.debug("Cleaning up memory-enabled assistant")
        if self._memory_manager:
            self._memory_manager.close()
        self._closed = True

    def __del__(self):
        """Cleanup resources during garbage collection."""
        self.close()

    async def on_messages(
        self,
        messages: Sequence[AutogenChatMessage|AgentMessage],
        cancellation_token: CancellationToken
    ) -> Response:
        # """Process messages with memory integration."""
        # # Initialize memory if needed
        # if self._memory_manager and not self._memory:
        #     await self.initialize_memory()
        #     print("DEBUG: Got memory instance with context")

        return await super().on_messages(messages, cancellation_token)
