"""Memory-enabled Anthropic chat completion client using mem0."""

import logging
import uuid
from typing import Any, Dict, List, Optional, Sequence, Union, AsyncGenerator, Mapping
from autogen_core.components import FunctionCall
from autogen_core.components.models import (
    ChatCompletionClient,
    LLMMessage,
    CreateResult,
    RequestUsage,
    ModelCapabilities,
)
from autogen_core.components.tools import Tool, ToolSchema
from autogen_core.base import CancellationToken

from mem0.proxy.main import Mem0

from autogen_mem0.core.messaging import (
    AssistantMessage,
    UserMessage,
    FunctionExecutionResultMessage,
    ToolCallMessage,
    ToolCallResultMessage,
    SystemMessage,
)


# Set up logging
logger = logging.getLogger(__name__)

class Mem0AnthropicChatCompletionClient(ChatCompletionClient):
    """Chat completion client using Mem0's proxy with memory integration."""

    def __init__(
            self,
            memory_config: Dict,
            user_id: Optional[str] = None,
            agent_id: Optional[str] = None,
            session_id: Optional[str] = None,
            enable_memory: bool = True,  # Add flag to control memory operations
            **kwargs: Any
        ):
        """Initialize the client.
        
        Args:
            memory_config: Raw memory configuration dictionary for mem0
            user_id: User ID for memory operations
            agent_id: Agent ID for memory operations
            session_id: Session ID for memory operations
            enable_memory: Whether to enable memory operations
            **kwargs: Additional arguments passed to Mem0
        """
        self._max_tokens = kwargs.get("max_tokens", 1024)
        
        # Initialize mem0 with raw config dict
        self._mem0 = Mem0(config=memory_config)
        
        # Store model name from config
        self._model = memory_config.get("llm", {}).get("config", {}).get("model")
        if not self._model:
            raise ValueError("Model name must be specified in memory_config.llm.config")
        
        # Store session identifiers
        self._user_id = user_id or str(uuid.uuid4())
        self._agent_id = agent_id or str(uuid.uuid4())
        self._session_id = session_id or str(uuid.uuid4())
        self._enable_memory = enable_memory
        
        logger.info(f"Initialized mem0 client with user_id={self._user_id}, agent_id={self._agent_id}, session_id={self._session_id}")
        
        # Track usage
        self._actual_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        
        
    async def create(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        """Create a chat completion with optional memory integration."""
        # Convert messages to mem0 format
        mem0_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                mem0_messages.append({
                    "role": "system",
                    "content": msg.content
                })
            elif isinstance(msg, UserMessage):
                mem0_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif isinstance(msg, AssistantMessage):
                mem0_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
            elif isinstance(msg, FunctionExecutionResultMessage):
                mem0_messages.append({
                    "role": "function",
                    "name": msg.name,
                    "content": msg.content
                })
            elif isinstance(msg, ToolCallMessage):
                mem0_messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "name": msg.name,
                })
            elif isinstance(msg, ToolCallResultMessage):
                mem0_messages.append({
                    "role": "tool",
                    "name": msg.name,
                    "content": msg.content
                })

        # Ensure first non-system message is a user message for Anthropic
        if not mem0_messages:
            mem0_messages.append({"role": "user", "content": "."})
        elif all(msg["role"] == "system" for msg in mem0_messages):
            mem0_messages.append({"role": "user", "content": "."})
        
        # Get memory parameters from extra_create_args
        memory_args = {}
        if self._enable_memory:
            memory_args.update({
                "user_id": extra_create_args.get("user_id", self._user_id),
                "agent_id": extra_create_args.get("agent_id", self._agent_id),
                "run_id": extra_create_args.get("run_id", self._session_id),
                "metadata": extra_create_args.get("metadata"),
                "filters": extra_create_args.get("filters"),
                "limit": extra_create_args.get("limit", 10),
            })
        
        try:
            # Create completion through mem0 (synchronous call)
            logger.debug(f"Creating completion with model={self._model}, user_id={memory_args.get('user_id')}, agent_id={memory_args.get('agent_id')}, run_id={memory_args.get('run_id')}")
            response = self._mem0.chat.completions.create(
                model=self._model,  # Use stored model name
                messages=mem0_messages,
                **memory_args,
                max_tokens=self._max_tokens,
                tools=tools,
                **extra_create_args
            )
            
            logger.debug(f"Received response: {response}")
            
            # Update usage tracking
            self._actual_usage = RequestUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )
            self._total_usage.prompt_tokens += response.usage.prompt_tokens
            self._total_usage.completion_tokens += response.usage.completion_tokens
            
            # Handle tool calls if present
            content: Union[str, List[FunctionCall]] = response.choices[0].message.content
            if hasattr(response.choices[0].message, "tool_calls") and response.choices[0].message.tool_calls:
                tool_calls = []
                for tool_call in response.choices[0].message.tool_calls:
                    # Generate a unique ID for each function call
                    tool_calls.append(FunctionCall(
                        id=str(uuid.uuid4()),  # Generate unique ID for each function call
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    ))
                content = tool_calls
            
            # Create result
            return CreateResult(
                content=content,
                usage=self._actual_usage,
                finish_reason=response.choices[0].finish_reason,
                cached=False  # Mem0 doesn't support caching currently
            )
            
        except Exception as e:
            logger.error(f"Error creating completion: {str(e)}", exc_info=True)
            raise
            
    async def create_stream(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> AsyncGenerator[Union[str, CreateResult], None]:
        """Create a streaming chat completion."""
        # For now, just use non-streaming version
        result = await self.create(
            messages=messages,
            tools=tools,
            json_output=json_output,
            extra_create_args=extra_create_args,
            cancellation_token=cancellation_token,
        )
        yield result
        
    def actual_usage(self) -> RequestUsage:
        """Get token usage for last request."""
        return self._actual_usage
    
    def total_usage(self) -> RequestUsage:
        """Get total token usage."""
        return self._total_usage
        
    def count_tokens(self, messages: Sequence[LLMMessage], tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Count tokens in messages and tools."""
        # TODO: Implement token counting
        return 0
        
    def remaining_tokens(self, messages: Sequence[LLMMessage], tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Get remaining tokens for context window."""
        # TODO: Implement remaining token calculation
        return self._max_tokens - self.count_tokens(messages, tools)
    
    @property
    def capabilities(self) -> ModelCapabilities:
        """Get model capabilities."""
        return ModelCapabilities(
            vision=True,  # Claude 3 supports vision
            function_calling=True,  # Supports function/tool calls
            json_output=True,  # Can output structured JSON
        )
