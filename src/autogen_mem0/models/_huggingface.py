"""HuggingFace chat completion client implementation."""

import os
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional, Sequence, Union
from typing_extensions import Unpack

import torch
from pydantic import BaseModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextIteratorStreamer,
    GenerationConfig,
)

from autogen_core.base import CancellationToken
from autogen_core.components.models import (
    ChatCompletionClient,
    CreateResult,
    LLMMessage,
    ModelCapabilities,
    RequestUsage,
)
from autogen_core.components.tools import Tool, ToolSchema

class HuggingFaceClientConfiguration(BaseModel):
    """Configuration for HuggingFace client."""
    model_name: str
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype: str = "auto"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    model_capabilities: Optional[ModelCapabilities] = None
    use_auth_token: Optional[str] = None

class HuggingFaceChatCompletionClient(ChatCompletionClient):
    """Chat completion client for HuggingFace transformer models."""
    
    def __init__(self, **kwargs: Unpack[HuggingFaceClientConfiguration]):
        if "model_name" not in kwargs:
            raise ValueError("model_name is required for HuggingFaceChatCompletionClient")
            
        self._raw_config = dict(kwargs).copy()
        self._model_capabilities = kwargs.get("model_capabilities")
        
        # Get auth token from config
        auth_token = kwargs.get("use_auth_token")
        if not auth_token:
            raise ValueError("use_auth_token must be provided in config")
            
        # Load model and tokenizer
        self._model = AutoModelForCausalLM.from_pretrained(
            kwargs["model_name"],
            device_map=kwargs.get("device", "auto"),
            torch_dtype=kwargs.get("torch_dtype", "auto"),
            use_auth_token=auth_token,
            trust_remote_code=True,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(
            kwargs["model_name"],
            use_auth_token=auth_token,
            trust_remote_code=True,
        )
        
        # Store generation config
        self._generation_config = GenerationConfig(
            max_new_tokens=kwargs.get("max_tokens"),
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 0.95),
            pad_token_id=self._tokenizer.eos_token_id,
        )
        
        # Usage tracking
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._last_prompt_tokens = 0
        self._last_completion_tokens = 0
        
    def __getstate__(self) -> Dict[str, Any]:
        """Get state for pickling."""
        state = self.__dict__.copy()
        state["_model"] = None
        state["_tokenizer"] = None
        return state
        
    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Set state for unpickling."""
        self.__dict__.update(state)
        # Get auth token from config
        auth_token = state["_raw_config"].get("use_auth_token")
        if not auth_token:
            raise ValueError("use_auth_token must be provided in config")
            
        self._model = AutoModelForCausalLM.from_pretrained(
            state["_raw_config"]["model_name"],
            device_map=state["_raw_config"].get("device", "auto"),
            torch_dtype=state["_raw_config"].get("torch_dtype", "auto"),
            use_auth_token=auth_token,
            trust_remote_code=True,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(
            state["_raw_config"]["model_name"],
            use_auth_token=auth_token,
            trust_remote_code=True,
        )

    def _convert_messages(self, messages: Sequence[LLMMessage]) -> str:
        """Convert messages to model input format."""
        system_message = None
        conversation = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                conversation.append({"role": msg.role, "content": msg.content})
                
        # Format as chat template if model supports it
        if self._tokenizer.chat_template:
            messages_dict = [{"role": "system", "content": system_message}] if system_message else []
            messages_dict.extend(conversation)
            return self._tokenizer.apply_chat_template(
                messages_dict,
                tokenize=False,
                add_generation_prompt=True
            )
            
        # Otherwise format manually
        formatted = ""
        if system_message:
            formatted += f"System: {system_message}\n\n"
            
        for msg in conversation:
            role = "Assistant" if msg["role"] == "assistant" else "Human"
            formatted += f"{role}: {msg['content']}\n"
            
        formatted += "Assistant:"
        return formatted
        
    async def create(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        """Create a chat completion."""
        prompt = self._convert_messages(messages)
        
        create_args = {}
        
        if json_output:
            if not self.capabilities["supports_json_output"]:
                raise ValueError("Model does not support JSON output")
            create_args["response_format"] = {"type": "json_object"}
            
        if tools:
            if not self.capabilities["supports_functions"]:
                raise ValueError("Model does not support function calling")
            create_args["tools"] = [
                {"name": t.name, "description": t.description} 
                for t in tools
            ]
            
        try:
            # Encode input
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
            self._last_prompt_tokens = len(inputs.input_ids[0])
            self._total_prompt_tokens += self._last_prompt_tokens
            
            # Generate
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    generation_config=self._generation_config,
                    **extra_create_args,
                    **create_args
                )
                
            # Decode output
            output_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            response_text = output_text[len(prompt):].strip()
            
            # Update completion tokens
            self._last_completion_tokens = len(outputs[0]) - len(inputs.input_ids[0])
            self._total_completion_tokens += self._last_completion_tokens
            
            return CreateResult(
                content=response_text,
                role="assistant",
                tool_calls=None,  # TODO: Add tool call parsing
            )
            
        except Exception as e:
            raise RuntimeError(f"Error creating chat completion: {str(e)}")
            
    async def create_stream(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> AsyncGenerator[Union[str, CreateResult], None]:
        """Create a streaming chat completion."""
        prompt = self._convert_messages(messages)
        
        create_args = {}
        
        if json_output:
            if not self.capabilities["supports_json_output"]:
                raise ValueError("Model does not support JSON output")
            create_args["response_format"] = {"type": "json_object"}
            
        if tools:
            if not self.capabilities["supports_functions"]:
                raise ValueError("Model does not support function calling")
            create_args["tools"] = [
                {"name": t.name, "description": t.description} 
                for t in tools
            ]
            
        try:
            # Encode input
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
            self._last_prompt_tokens = len(inputs.input_ids[0])
            self._total_prompt_tokens += self._last_prompt_tokens
            
            # Setup streamer
            streamer = TextIteratorStreamer(
                self._tokenizer,
                skip_prompt=True,
                skip_special_tokens=True
            )
            
            # Generate in background
            generation_kwargs = {
                **inputs,
                "generation_config": self._generation_config,
                **extra_create_args,
                **create_args,
                "streamer": streamer,
            }
            
            with torch.no_grad():
                self._model.generate(**generation_kwargs)
                
            # Stream tokens
            async for text in streamer:
                yield text
                
            # Update completion tokens
            self._last_completion_tokens = len(streamer.tokens)
            self._total_completion_tokens += self._last_completion_tokens
                
        except Exception as e:
            raise RuntimeError(f"Error creating streaming chat completion: {str(e)}")
            
    def actual_usage(self) -> RequestUsage:
        """Get the token usage for the last request."""
        return RequestUsage(
            prompt_tokens=self._last_prompt_tokens,
            completion_tokens=self._last_completion_tokens,
        )
        
    def total_usage(self) -> RequestUsage:
        """Get the total token usage across all requests."""
        return RequestUsage(
            prompt_tokens=self._total_prompt_tokens,
            completion_tokens=self._total_completion_tokens,
        )
        
    def count_tokens(self, messages: Sequence[LLMMessage], tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Count the number of tokens in the input."""
        prompt = self._convert_messages(messages)
        
        if tools:
            tool_descriptions = "\n".join(
                f"- {t.name}: {t.description}" 
                for t in tools
            )
            prompt += f"\nYou have access to the following tools:\n{tool_descriptions}\n"
            
        return len(self._tokenizer.encode(prompt))
        
    def remaining_tokens(self, messages: Sequence[LLMMessage], tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Get the number of tokens remaining for the response."""
        used_tokens = self.count_tokens(messages, tools)
        model_context = self._model_capabilities.context_window if self._model_capabilities else 2048
        return model_context - used_tokens
        
    def _get_default_capabilities(self) -> Dict[str, Any]:
        """Get default capabilities."""
        return {
            "context_window": 2048,  # Conservative default
            "supports_functions": False,  # Not yet implemented
            "supports_json_output": True,
            "supports_streaming": True,
            "supports_vision": False,
        }
        
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get the model capabilities."""
        if self._model_capabilities:
            return self._model_capabilities.__dict__
            
        # Default capabilities
        return self._get_default_capabilities()
