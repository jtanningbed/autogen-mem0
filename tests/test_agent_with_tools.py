import asyncio
import json
from datetime import datetime
from typing import List

from autogen_agentchat.agents import (
    Agent,
    GroupChat,
    GroupChatManager,
    GroupChatMessage,
    RequestToSpeak,
)
from autogen_core.components.models import UserMessage
from autogen_core.components.tools import Tool, ToolSchema
from anthropic_autogen.models import AnthropicChatCompletionClient

# Define some example tools
async def get_current_time() -> str:
    """Get the current time."""
    return datetime.now().strftime("%H:%M:%S")

async def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)

async def test_agent_with_tools():
    # Initialize the Anthropic client
    client = AnthropicChatCompletionClient(
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=1024,
    )
    
    # Create tools
    time_tool = Tool(
        name="get_current_time",
        description="Get the current time",
        function=get_current_time,
    )
    
    calc_tool = Tool(
        name="calculate_sum",
        description="Calculate the sum of numbers",
        function=calculate_sum,
        parameters={
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of numbers to sum"
                }
            },
            "required": ["numbers"]
        }
    )
    
    # Create an agent with tools
    assistant = Agent(
        id="Assistant",
        description="An assistant that can use tools to help with tasks.",
        model_client=client,
        system_message="You are a helpful assistant that can use tools to accomplish tasks. "
                      "Use the get_current_time tool to tell time and calculate_sum to add numbers.",
        tools=[time_tool, calc_tool]
    )
    
    # Create group chat
    group_chat = GroupChat(
        agents=[assistant],
        messages=[],
        max_round=5,
        topic_type="tool_usage"
    )
    
    # Start conversation
    await group_chat.start()
    
    # Test time tool
    message1 = GroupChatMessage(
        body=UserMessage(content="What time is it right now?", source="user"),
        topic_id=group_chat.topic_id,
    )
    await group_chat.publish_message(message1)
    await group_chat.wait_for_completion()
    
    # Test calculator tool
    message2 = GroupChatMessage(
        body=UserMessage(content="What is the sum of 1.5, 2.5, and 3.5?", source="user"),
        topic_id=group_chat.topic_id,
    )
    await group_chat.publish_message(message2)
    await group_chat.wait_for_completion()

if __name__ == "__main__":
    asyncio.run(test_agent_with_tools())
