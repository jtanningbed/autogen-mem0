"""Test agent conversation scenarios."""

import logging
from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.application.logging import TRACE_LOGGER_NAME
from autogen_core.base import (
    MessageContext,
    AgentId
)
from autogen_core.components import (
    message_handler,
)

from anthropic_autogen.core.messaging import ChatMessage
from anthropic_autogen.core.agents import BaseAgent

# Configure logging
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.setLevel(logging.INFO)

class DumbAgent(BaseAgent):
    """Agent that can participate in conversations."""

    def __init__(self, description: str, smart_agent_type: str):
        """Initialize conversation agent."""
        super().__init__(description=description)
        self.smart_agent_id = AgentId(smart_agent_type, self.id.key)
        logger.info(f"{description} initialized")

    @message_handler
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> ChatMessage:
        logger.info(f"Hi This is Agent A. I received a message: {message.content}")
        logger.info("I am unsure about this question. Let me ask Agent B.")
        response = await self.send_message(message, self.smart_agent_id)
        return response

class SmartAgent(BaseAgent):
    def __init__(self, description: str):
        super().__init__(description=description)
        logger.info(f"Agent {description} initialized")

    @message_handler
    async def handle_chat(
        self, message: ChatMessage, ctx: MessageContext
    ) -> ChatMessage:
        logger.info(f"This is Agent B. I received the question: {message.content}")
        logger.info("The capital of France is Paris.")
        return ChatMessage(content="The capital of France is Paris.")


class TestRequestResponseConversation:
    """Test realistic conversation scenarios."""

    async def test_simple_qa(
            self,
            runtime: SingleThreadedAgentRuntime,
            test_topic_type: str
        ):
        """Test simple question-answer scenario."""
        logger.info("\n=== Starting test_simple_qa ===")

        # Register agents with their ids
        await SmartAgent.register(
            runtime, "smart_agent", lambda: SmartAgent(description="Agent B")
        )

        await DumbAgent.register(
            runtime, "dumb_agent", lambda: DumbAgent(description="Agent A", smart_agent_type="smart_agent")
        )

        # Start the runtime
        runtime.start()

        dumb_agent_id = AgentId("dumb_agent", "default")

        # Set up expected response for agent B
        expected_question = "What is the capital of France?"
        expected_answer = "The capital of France is Paris."

        # Send message to group chat topic
        question_msg = ChatMessage(
            content=expected_question
        )
        logger.info(
            f"\Sending question: {question_msg.content} from runtime to the dumb agent."
        )
        response = await runtime.send_message(question_msg, dumb_agent_id)

        await runtime.stop_when_idle()
        assert response.content == expected_answer

    # async def test_group_chat(
    #         self,
    #         runtime: SingleThreadedAgentRuntime,
    #         test_topic_type: str
    #     ):
    #     """Test group chat scenario with multiple agents."""
    #     print("\n=== Starting test_group_chat ===")

    #     # Start the runtime
    #     runtime.start()

    #     # Define topic types
    #     group_chat_topic = test_topic_type
    #     agents = {}
    #     agent_instances = {}

    #     # Create three agents
    #     agent_names = ["Moderator", "Expert", "Assistant"]
    #     for name in agent_names:
    #         agent_type = f"agent_{name.lower()}"
    #         agent = await ConversationAgent.register(
    #             runtime,
    #             agent_type,
    #             lambda n=name: ConversationAgent(
    #                 description=n,
    #                 group_chat_topic_type=group_chat_topic
    #             )
    #         )
    #         agents[name] = agent
    #         print(f"Registered agent: {agent}")

    #         # Subscribe to group chat topic
    #         await runtime.add_subscription(
    #             TypeSubscription(topic_type=group_chat_topic, agent_type=agent.type)
    #         )

    #         # Get agent instance for verification
    #         agent_id = AgentId(type=agent.type, key="default")
    #         agent_instances[name] = await runtime._get_agent(agent_id)

    #     # Set up expected responses
    #     moderator_id = AgentId(type=agents["Moderator"].type, key="default")
    #     expert_id = AgentId(type=agents["Expert"].type, key="default")
    #     assistant_id = AgentId(type=agents["Assistant"].type, key="default")

    #     # Configure expected responses
    #     question_1 = "What are the key benefits of Python?"
    #     answer_1 = "Python offers readability, extensive libraries, and cross-platform support."
    #     question_2 = "Can you provide examples of Python's cross-platform support?"
    #     answer_2 = "Python runs on Windows, macOS, Linux, and many other platforms. You can write once, run anywhere."

    #     agent_instances["Expert"].expect_response(question_1, answer_1)
    #     agent_instances["Assistant"].expect_response(question_2, answer_2)

    #     # Start the group discussion
    #     messages = [
    #         (moderator_id, question_1, agents["Expert"].type),
    #         (expert_id, question_2, agents["Assistant"].type)
    #     ]

    #     for sender_id, content, recipient_type in messages:
    #         message = ChatMessage(
    #             content=content,
    #             sender=sender_id.type,
    #             recipient=recipient_type
    #         )
    #         topic_id = TopicId(type=group_chat_topic, source=sender_id.type)
    #         print(f"\nPublishing message: {content} from {sender_id.type} to {recipient_type}")
    #         await runtime.publish_message(message, topic_id, sender=sender_id)

    #         # Give time for message processing
    #         await asyncio.sleep(1.0)

    #         # Print message records for debugging
    #         print("\nMessage Records after sending:", content)
    #         for name, agent in agent_instances.items():
    #             print(f"\n{name} received messages:")
    #             for msg in agent.received_messages:
    #                 print(f"  From: {msg.sender}, Content: {msg.content}")
    #             print(f"\n{name} sent messages:")
    #             for msg in agent.sent_messages:
    #                 print(f"  To: {msg.recipient}, Content: {msg.content}")

    #     # Stop the runtime when idle
    #     await runtime.stop_when_idle()

    #     # Verify group chat message flow
    #     # 1. Verify Expert received moderator's question
    #     assert any(msg.content == question_1 and msg.sender == agents["Moderator"].type
    #               for msg in agent_instances["Expert"].received_messages), \
    #         "Expert did not receive moderator's question"

    #     # 2. Verify Expert sent the correct response
    #     assert any(msg.content == answer_1
    #               for msg in agent_instances["Expert"].sent_messages), \
    #         "Expert did not send expected response"

    #     # 3. Verify Assistant received Expert's question
    #     assert any(msg.content == question_2 and msg.sender == agents["Expert"].type
    #               for msg in agent_instances["Assistant"].received_messages), \
    #         "Assistant did not receive expert's question"

    #     # 4. Verify Assistant sent the correct response
    #     assert any(msg.content == answer_2
    #               for msg in agent_instances["Assistant"].sent_messages), \
    #         "Assistant did not send expected response"

    #     # 5. Verify all agents received all messages (group chat functionality)
    #     for name, agent in agent_instances.items():
    #         assert len(agent.received_messages) >= 2, \
    #             f"{name} did not receive all group chat messages"

    #     # 6. Verify message ordering for all agents
    #     for name, agent in agent_instances.items():
    #         for i in range(1, len(agent.received_messages)):
    #             assert agent.received_messages[i].timestamp >= agent.received_messages[i-1].timestamp, \
    #                 f"Messages received out of order for {name}"
