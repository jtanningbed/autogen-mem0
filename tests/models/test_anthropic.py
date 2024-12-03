import pytest
import asyncio
import os
import logging
from typing import List, Sequence
from decimal import Decimal, ROUND_HALF_UP

from autogen_mem0.core.messaging import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
)
from autogen_core.components.models import CreateResult
from autogen_mem0.models import AnthropicChatCompletionClient
from autogen_mem0.models._model_info import calculate_cost, get_model_pricing

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug logging for our module
logging.getLogger('autogen_mem0').setLevel(logging.DEBUG)

@pytest.fixture
async def client() -> AnthropicChatCompletionClient:
    """Fixture to create an Anthropic client for tests."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    return AnthropicChatCompletionClient(
        api_key=api_key,
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=1024,
    )

@pytest.fixture
def basic_messages() -> Sequence[Message]:
    """Fixture for a basic message list."""
    return [
        SystemMessage(content="You are a helpful AI assistant."),
        UserMessage(content="What is the capital of France?", source="user")
    ]

@pytest.mark.asyncio
async def test_simple_completion(
    client: AnthropicChatCompletionClient,
    basic_messages: Sequence[Message]
) -> None:
    """Test basic completion functionality."""
    result = await client.create(basic_messages)
    
    assert result is not None
    assert isinstance(result, CreateResult)
    assert isinstance(result.content, str)
    assert len(result.content) > 0
    assert "paris" in result.content.lower()

@pytest.mark.asyncio
async def test_streaming_completion(
    client: AnthropicChatCompletionClient,
    basic_messages: Sequence[Message]
) -> None:
    """Test streaming completion functionality."""
    chunks = []
    async for chunk in client.create_stream(basic_messages):
        assert isinstance(chunk, (str, CreateResult))
        if isinstance(chunk, str):
            chunks.append(chunk)
        else:
            chunks.append(chunk.content)
    
    complete_response = "".join(chunks)
    assert len(complete_response) > 0
    assert "paris" in complete_response.lower()

@pytest.mark.asyncio
async def test_multiple_messages(client: AnthropicChatCompletionClient) -> None:
    """Test conversation with multiple back-and-forth messages."""
    messages: Sequence[Message] = [
        SystemMessage(content="You are a helpful AI assistant."),
        UserMessage(content="Let's do a math problem.", source="user"),
        UserMessage(content="What is 2 + 2?", source="user")
    ]
    
    result = await client.create(messages)
    assert "4" in result.content

@pytest.mark.asyncio
async def test_long_conversation(client: AnthropicChatCompletionClient) -> None:
    """Test handling of a longer conversation."""
    messages: Sequence[Message] = [
        SystemMessage(content="You are a helpful AI assistant."),
        UserMessage(content="Tell me about Python.", source="user"),
        UserMessage(content="What are its main features?", source="user"),
        UserMessage(content="Give me an example of list comprehension.", source="user")
    ]
    
    result = await client.create(messages)
    assert len(result.content) > 0
    assert "list comprehension" in result.content.lower()

@pytest.mark.asyncio
async def test_empty_messages(client: AnthropicChatCompletionClient) -> None:
    """Test handling of empty messages list."""
    with pytest.raises(Exception):  
        await client.create([])

@pytest.mark.asyncio
async def test_invalid_message_type(client: AnthropicChatCompletionClient) -> None:
    """Test handling of invalid message type."""
    messages = [{"content": "This is not a valid message type"}]  
    
    with pytest.raises(Exception):
        await client.create(messages)

@pytest.mark.asyncio
async def test_temperature_affects_output(
    client: AnthropicChatCompletionClient
) -> None:
    """Test that different temperature values produce different outputs."""
    messages: Sequence[Message] = [
        SystemMessage(content="You are a helpful AI assistant."),
        UserMessage(content="Tell me a creative story about a magical forest. Make it unique and different each time.", source="user")
    ]
    
    # Create two clients with different temperatures
    client1 = AnthropicChatCompletionClient(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229",
        temperature=0.0,
        max_tokens=1024,
    )
    
    client2 = AnthropicChatCompletionClient(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229",
        temperature=1.0,
        max_tokens=1024,
    )
    
    result1 = await client1.create(messages)
    result2 = await client2.create(messages)
    
    # The responses should be different due to temperature difference
    assert result1.content != result2.content

@pytest.mark.asyncio
async def test_cost_calculation() -> None:
    """Test cost calculation for requests."""
    # Test direct cost calculation
    model = "claude-3-sonnet-20240229"
    input_tokens = 100
    output_tokens = 50
    
    # Calculate expected cost
    pricing = get_model_pricing(model)
    expected_cost = (
        (input_tokens / 1_000_000) * pricing["input_price_per_mtok"] +
        (output_tokens / 1_000_000) * pricing["output_price_per_mtok"]
    )
    
    # Calculate actual cost
    actual_cost = calculate_cost(model, input_tokens, output_tokens)
    
    # Use Decimal for precise comparison
    assert Decimal(str(actual_cost)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP) == \
           Decimal(str(expected_cost)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

@pytest.mark.asyncio
async def test_client_cost_tracking(client: AnthropicChatCompletionClient) -> None:
    """Test cost tracking in the client."""
    messages: Sequence[Message] = [
        SystemMessage(content="You are a helpful AI assistant."),
        UserMessage(content="Say 'hello' in exactly one word.", source="user")
    ]
    
    # First request
    result1 = await client.create(messages)
    assert client.last_request_cost > 0, "Cost should be greater than 0"
    first_request_cost = client.last_request_cost
    first_total_cost = client.total_cost
    
    # Second request
    result2 = await client.create(messages)
    assert client.last_request_cost > 0, "Cost should be greater than 0"
    second_request_cost = client.last_request_cost
    
    # Verify total cost is sum of both requests
    assert abs(client.total_cost - (first_request_cost + second_request_cost)) < 0.000001, \
           "Total cost should be sum of individual request costs"
    assert client.total_cost > first_total_cost, "Total cost should increase with each request"

@pytest.mark.asyncio
async def test_cost_with_different_models() -> None:
    """Test cost calculation with different models."""
    messages: Sequence[Message] = [
        SystemMessage(content="You are a helpful AI assistant."),
        UserMessage(content="Say 'hello' in exactly one word.", source="user")
    ]
    
    # Test with different models
    models = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
    
    costs = {}
    for model in models:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY environment variable not set")
        
        client = AnthropicChatCompletionClient(
            api_key=api_key,
            model=model,
            temperature=0.7,
            max_tokens=1024,
        )
        
        result = await client.create(messages)
        costs[model] = client.last_request_cost
    
    # Verify relative costs (Opus > Sonnet > Haiku)
    assert costs["claude-3-opus-20240229"] > costs["claude-3-sonnet-20240229"], \
           "Opus should cost more than Sonnet"
    assert costs["claude-3-sonnet-20240229"] > costs["claude-3-haiku-20240307"], \
           "Sonnet should cost more than Haiku"
