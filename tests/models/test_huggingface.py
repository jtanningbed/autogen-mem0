"""Tests for the HuggingFace chat completion client."""

import os
import pytest
from typing import Generator
import torch

from anthropic_autogen.models._huggingface import (
    HuggingFaceChatCompletionClient,
    HuggingFaceClientConfiguration,
)
from autogen_core.components.models import (
    LLMMessage,
    ModelCapabilities,
)

@pytest.fixture
def mock_model(mocker):
    """Mock HuggingFace model."""
    mock = mocker.MagicMock()
    mock.device = torch.device("cpu")
    mock.generate.return_value = torch.tensor([[1, 2, 3]])
    return mock

@pytest.fixture
def mock_tokenizer(mocker):
    """Mock HuggingFace tokenizer."""
    mock = mocker.MagicMock()
    mock.chat_template = None
    mock.encode.return_value = [1, 2, 3]
    mock.decode.return_value = "Test response"
    mock.eos_token_id = 2
    return mock

@pytest.fixture
def mock_auto_model(mocker, mock_model):
    """Mock AutoModelForCausalLM."""
    mock_auto = mocker.patch("anthropic_autogen.models._huggingface.AutoModelForCausalLM")
    mock_auto.from_pretrained.return_value = mock_model
    return mock_auto

@pytest.fixture
def mock_auto_tokenizer(mocker, mock_tokenizer):
    """Mock AutoTokenizer."""
    mock_auto = mocker.patch("anthropic_autogen.models._huggingface.AutoTokenizer")
    mock_auto.from_pretrained.return_value = mock_tokenizer
    return mock_auto

@pytest.fixture
def client(mock_auto_model, mock_auto_tokenizer):
    """Create test client."""
    return HuggingFaceChatCompletionClient(
        model_name="test/model",
        device="cpu",
        max_tokens=100,
        temperature=0.7,
    )

def test_init_requires_model_name():
    """Test that model_name is required."""
    with pytest.raises(ValueError):
        HuggingFaceChatCompletionClient()

def test_init_loads_model_and_tokenizer(mock_auto_model, mock_auto_tokenizer):
    """Test that model and tokenizer are loaded correctly."""
    client = HuggingFaceChatCompletionClient(model_name="test/model")
    
    mock_auto_model.from_pretrained.assert_called_once()
    mock_auto_tokenizer.from_pretrained.assert_called_once()

def test_init_uses_auth_token(mock_auto_model, mock_auto_tokenizer, monkeypatch):
    """Test that auth token is used correctly."""
    monkeypatch.setenv("HUGGINGFACE_TOKEN", "test-token")
    
    client = HuggingFaceChatCompletionClient(model_name="test/model")
    
    mock_auto_model.from_pretrained.assert_called_with(
        "test/model",
        device_map="auto",
        torch_dtype="auto",
        use_auth_token="test-token",
        trust_remote_code=True,
    )

def test_convert_messages_basic(client):
    """Test basic message conversion."""
    messages = [
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi"),
    ]
    
    result = client._convert_messages(messages)
    
    assert "Human: Hello" in result
    assert "Assistant: Hi" in result
    assert result.endswith("Assistant:")

def test_convert_messages_with_system(client):
    """Test message conversion with system message."""
    messages = [
        LLMMessage(role="system", content="Be helpful"),
        LLMMessage(role="user", content="Hello"),
    ]
    
    result = client._convert_messages(messages)
    
    assert "System: Be helpful" in result
    assert "Human: Hello" in result

def test_convert_messages_with_template(client, mock_tokenizer):
    """Test message conversion with chat template."""
    mock_tokenizer.chat_template = True
    mock_tokenizer.apply_chat_template.return_value = "Template output"
    
    messages = [
        LLMMessage(role="user", content="Hello"),
    ]
    
    result = client._convert_messages(messages)
    
    assert result == "Template output"
    mock_tokenizer.apply_chat_template.assert_called_once()

@pytest.mark.asyncio
async def test_create(client):
    """Test create method."""
    messages = [LLMMessage(role="user", content="Hello")]
    
    result = await client.create(messages)
    
    assert result.content == "Test response"
    assert result.role == "assistant"
    assert result.tool_calls is None

@pytest.mark.asyncio
async def test_create_with_tools(client):
    """Test create method with tools."""
    messages = [LLMMessage(role="user", content="Hello")]
    tools = [
        {
            "name": "test_tool",
            "description": "A test tool",
        }
    ]
    
    result = await client.create(messages, tools=tools)
    
    assert result.content == "Test response"
    assert "test_tool" in client._convert_messages(messages)

@pytest.mark.asyncio
async def test_create_stream(client, mock_tokenizer):
    """Test create_stream method."""
    messages = [LLMMessage(role="user", content="Hello")]
    
    stream = client.create_stream(messages)
    chunks = [chunk async for chunk in stream]
    
    assert len(chunks) > 0
    assert isinstance(chunks[0], str)

def test_token_counting(client):
    """Test token counting methods."""
    messages = [LLMMessage(role="user", content="Hello")]
    
    count = client.count_tokens(messages)
    assert count == 3  # Length of mock encode output
    
    remaining = client.remaining_tokens(messages)
    assert remaining == 2045  # 2048 - 3

def test_usage_tracking(client):
    """Test usage tracking."""
    assert client.actual_usage().prompt_tokens == 0
    assert client.actual_usage().completion_tokens == 0
    assert client.total_usage().prompt_tokens == 0
    assert client.total_usage().completion_tokens == 0

def test_capabilities(client):
    """Test capabilities property."""
    caps = client.capabilities
    
    assert isinstance(caps, ModelCapabilities)
    assert caps.context_window == 2048
    assert not caps.supports_functions
    assert caps.supports_json_output
    assert caps.supports_streaming

def test_custom_capabilities(mock_auto_model, mock_auto_tokenizer):
    """Test custom capabilities."""
    custom_caps = ModelCapabilities(
        context_window=4096,
        supports_functions=True,
        supports_json_output=False,
        supports_streaming=False,
    )
    
    client = HuggingFaceChatCompletionClient(
        model_name="test/model",
        model_capabilities=custom_caps,
    )
    
    assert client.capabilities == custom_caps
