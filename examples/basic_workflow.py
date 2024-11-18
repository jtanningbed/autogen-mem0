"""
Example demonstrating basic workflow with anthropic-autogen components.
"""

import os
import asyncio
from anthropic_autogen.agents import (
    CodeAssistantAgent,
    WebUIUserProxy,
    WorkflowOrchestrator
)
from anthropic_autogen.core.messaging import ChatMessage
from anthropic_autogen.models import AnthropicChatCompletionClient
from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.base import AgentId, AgentType


async def main():
    # Initialize the LLM client with API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Please set ANTHROPIC_API_KEY environment variable")
        
    llm_client = AnthropicChatCompletionClient(
        api_key=api_key,
        model="claude-3-opus-20240229"
    )

    # Initialize runtime
    runtime = SingleThreadedAgentRuntime()
    
    # Create agent types
    code_assistant_type = AgentType("code_assistant")
    user_proxy_type = AgentType("user_proxy")
    orchestrator_type = AgentType("orchestrator")

    # Create agent IDs
    code_assistant_id = AgentId(key="code_assistant", type=code_assistant_type)
    user_proxy_id = AgentId(key="user", type=user_proxy_type)
    orchestrator_id = AgentId(key="orchestrator", type=orchestrator_type)

    # Register agent factories
    await runtime.register(
        type=code_assistant_type,
        agent_factory=lambda: CodeAssistantAgent(
            agent_id=code_assistant_id,
            name="Code Helper",
            description="AI assistant that helps with coding tasks",
            llm_client=llm_client
        )
    )
    
    await runtime.register(
        type=user_proxy_type,
        agent_factory=lambda: WebUIUserProxy(
            agent_id=user_proxy_id,
            name="Web UI",
            description="Web UI proxy agent"
        )
    )
    
    await runtime.register(
        type=orchestrator_type,
        agent_factory=lambda: WorkflowOrchestrator(
            agent_id=orchestrator_id,
            name="Workflow Manager",
            description="Coordinates workflow between agents",
            agents=[code_assistant_id, user_proxy_id]
        )
    )

    # Start runtime
    await runtime.start()

    try:
        # Get agent instances
        code_assistant = await runtime.get(code_assistant_id)
        user_proxy = await runtime.get(user_proxy_id)
        orchestrator = await runtime.get(orchestrator_id)

        # Example workflow: User requests code review
        message = ChatMessage(
            content="Can you help me review this Python code?\n\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```",
            sender=user_proxy_id.key,
            recipient=code_assistant_id.key
        )
        await user_proxy.send_message(message, to=code_assistant_id)

        # Let the workflow run for a while
        await asyncio.sleep(10)  # Reduced timeout for testing

    finally:
        # Cleanup
        await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
