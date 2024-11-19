import logging
from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.application.logging import TRACE_LOGGER_NAME
from autogen_core.base import MessageContext, AgentId, TopicId
from autogen_core.components import (
    message_handler,
    DefaultTopicId,
    default_subscription,
    TypeSubscription, 
    type_subscription
)

from anthropic_autogen.core.messaging import ChatMessage
from anthropic_autogen.core.agents import BaseAgent

# Configure logging
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.setLevel(logging.INFO)

@default_subscription
class BroadcastAgent(BaseAgent):
    """Agent that can participate in conversations."""

    def __init__(self, description: str):
        """Initialize conversation agent."""
        super().__init__(description=description)
        logger.info(f"{description} initialized")

    @message_handler
    async def handle_chat(
        self, message: ChatMessage, ctx: MessageContext
    ) -> None:
        logger.info(f"This is the broadcasting agent {self._description}. I received the message: {message.content}")
        logger.info("publishing a message from the broadcast agent")
        await self.publish_message(
            ChatMessage(content = "HELLO from broadcasting agent!"),
            topic_id=TopicId(type="receiver", source="broadcast_agent")
        )

@type_subscription(topic_type="receiver")
class ReceivingAgent(BaseAgent):
    def __init__(self, description: str):
        super().__init__(description=description)
        logger.info(f"{description} initialized")

    @message_handler
    async def handle_chat(
        self, message: ChatMessage, ctx: MessageContext
    ) -> None:
        logger.info(f"This is the receiving agent: {self._description}. I received the message: {message.content}")

class TestBroadcastConversation:
    async def test_broadcast(self, runtime: SingleThreadedAgentRuntime):
        logger.info("\n=== Starting test_broadcast ===")

        await ReceivingAgent.register(
            runtime,
            "agent_a",
            lambda: ReceivingAgent(description="Agent A"),
        )
        await ReceivingAgent.register(
            runtime,
            "agent_b",
            lambda: ReceivingAgent(description="Agent B"),
        )
        
        # Register agents with their ids
        await BroadcastAgent.register(
            runtime, "broadcast_agent", lambda: BroadcastAgent(description="Broadcasting agent")
        )

        # await runtime.add_subscription(TypeSubscription(topic_type="receiver", agent_type="agent_a"))

        # Start the runtime
        runtime.start()
        logger.info(f'Publishing message from the runtime...')
        await runtime.publish_message(
            ChatMessage(content="Hello from the runtime!"),
            topic_id=DefaultTopicId(),
        )

        await runtime.stop_when_idle()
