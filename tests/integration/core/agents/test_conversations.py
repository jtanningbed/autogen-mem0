"""Test agent conversation scenarios."""

import pytest
import logging
from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.base import (
    MessageContext,
    TopicId,
    MessageSerializer,
    AgentId,
    CancellationToken
)
from autogen_core.components import TypeSubscription, message_handler
from autogen_core.base._serialization import PydanticJsonMessageSerializer
from typing import Type, Tuple, Any, List, Dict
from dataclasses import dataclass, field
import asyncio

from anthropic_autogen.core.messaging import ChatMessage
from anthropic_autogen.core.agents import BaseAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class MessageRecord:
    """Record of a message sent or received."""
    content: str
    sender: str
    recipient: str
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())

class ConversationAgent(BaseAgent):
    """Agent that can participate in conversations."""

    def __init__(self, description: str, group_chat_topic_type: str = None):
        """Initialize conversation agent."""
        super().__init__(description=description)
        self._group_chat_topic_type = group_chat_topic_type
        self.expected_responses = {}
        self.received_messages: List[MessageRecord] = []
        self.sent_messages: List[MessageRecord] = []
        print(f"Agent {description} initialized")

    def expect_response(self, query: str, response: str):
        """Set expected response for a query."""
        self.expected_responses[query] = response

    @message_handler
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle chat message with predefined responses."""
        sender_id = ctx.sender
        sender_type = sender_id.type if sender_id else "unknown"
        print(f"Agent {self.type} handling chat message: {message.content} from {sender_type}")
        
        # Record received message
        self.received_messages.append(MessageRecord(
            content=message.content,
            sender=message.sender,  
            recipient=self.type
        ))

        # Only respond if we're the intended recipient
        if message.recipient == self.type and message.content in self.expected_responses:
            response = ChatMessage(
                content=self.expected_responses[message.content],
                sender=self.type,
                recipient=message.sender
            )
            
            # Record sent message before sending
            self.sent_messages.append(MessageRecord(
                content=response.content,
                sender=self.type,
                recipient=response.recipient
            ))
            
            print(f"Agent {self.type} sending response: {response.content} to {response.recipient}")
            # Always send responses to the group chat topic to maintain conversation flow
            topic_id = TopicId(type=self._group_chat_topic_type, source=self.type)
            await self.publish_message(response, topic_id)

    @classmethod
    def _handles_types(cls) -> List[Tuple[Type[Any], List[MessageSerializer[Any]]]]:
        """Get message types this agent handles."""
        return [
            (ChatMessage, [PydanticJsonMessageSerializer(ChatMessage)])
        ]


class TestConversationScenarios:
    """Test realistic conversation scenarios."""

    async def test_simple_qa(
            self,
            runtime: SingleThreadedAgentRuntime,
            test_topic_type: str
        ):
        """Test simple question-answer scenario."""
        print("\n=== Starting test_simple_qa ===")

        # Start the runtime
        runtime.start()

        # Define topic types
        agent_a_topic = "agent_a"
        agent_b_topic = "agent_b"
        group_chat_topic = test_topic_type

        # Register agents with their topic types
        agent_a = await ConversationAgent.register(
            runtime,
            agent_a_topic,
            lambda: ConversationAgent(
                description="Agent A",
                group_chat_topic_type=group_chat_topic
            )
        )
        agent_b = await ConversationAgent.register(
            runtime,
            agent_b_topic,
            lambda: ConversationAgent(
                description="Agent B",
                group_chat_topic_type=group_chat_topic
            )
        )
        print(f"Registered agents: {agent_a}, {agent_b}")

        # Add subscriptions for both individual and group topics
        await runtime.add_subscription(TypeSubscription(topic_type=agent_a_topic, agent_type=agent_a.type))
        await runtime.add_subscription(TypeSubscription(topic_type=group_chat_topic, agent_type=agent_a.type))
        await runtime.add_subscription(TypeSubscription(topic_type=agent_b_topic, agent_type=agent_b.type))
        await runtime.add_subscription(TypeSubscription(topic_type=group_chat_topic, agent_type=agent_b.type))

        # Set up expected response through direct message
        agent_b_id = AgentId(type=agent_b.type, key="default")
        agent_a_id = AgentId(type=agent_a.type, key="default")

        # Get agent instances for verification
        agent_a_instance = await runtime._get_agent(agent_a_id)
        agent_b_instance = await runtime._get_agent(agent_b_id)

        # Set up expected response for agent B
        expected_question = "What is the capital of France?"
        expected_answer = "The capital of France is Paris."
        agent_b_instance.expect_response(expected_question, expected_answer)

        # Send message to group chat topic
        setup_msg = ChatMessage(
            content=expected_question,
            sender=agent_a.type,
            recipient=agent_b.type
        )
        topic_id = TopicId(type=group_chat_topic, source=agent_a.type)
        print(f"\nPublishing question: {setup_msg.content} from {agent_a.type} to {agent_b.type}")
        await agent_a_instance.publish_message(setup_msg, topic_id)

        # Give time for message processing
        await asyncio.sleep(1.0)

        # Print message records for debugging
        print("\nMessage Records after Q&A:")
        for agent, instance in [("A", agent_a_instance), ("B", agent_b_instance)]:
            print(f"\nAgent {agent} received messages:")
            for msg in instance.received_messages:
                print(f"  From: {msg.sender}, Content: {msg.content}")
            print(f"\nAgent {agent} sent messages:")
            for msg in instance.sent_messages:
                print(f"  To: {msg.recipient}, Content: {msg.content}")

        # Verify message flow
        # 1. Check that Agent B received the question
        assert any(msg.content == expected_question and msg.sender == agent_a.type 
                  for msg in agent_b_instance.received_messages), "Agent B did not receive the question"

        # 2. Check that Agent B sent the correct response
        assert any(msg.content == expected_answer and msg.recipient == agent_a.type 
                  for msg in agent_b_instance.sent_messages), "Agent B did not send the expected response"

        # 3. Check message ordering
        for agent in [agent_a_instance, agent_b_instance]:
            for i in range(1, len(agent.received_messages)):
                assert agent.received_messages[i].timestamp >= agent.received_messages[i-1].timestamp, \
                    f"Messages received out of order for {agent.type}"

    async def test_group_chat(
            self,
            runtime: SingleThreadedAgentRuntime,
            test_topic_type: str
        ):
        """Test group chat scenario with multiple agents."""
        print("\n=== Starting test_group_chat ===")

        # Start the runtime
        runtime.start()

        # Define topic types
        group_chat_topic = test_topic_type
        agents = {}
        agent_instances = {}

        # Create three agents
        agent_names = ["Moderator", "Expert", "Assistant"]
        for name in agent_names:
            agent_type = f"agent_{name.lower()}"
            agent = await ConversationAgent.register(
                runtime,
                agent_type,
                lambda n=name: ConversationAgent(
                    description=n,
                    group_chat_topic_type=group_chat_topic
                )
            )
            agents[name] = agent
            print(f"Registered agent: {agent}")

            # Subscribe to group chat topic
            await runtime.add_subscription(
                TypeSubscription(topic_type=group_chat_topic, agent_type=agent.type)
            )

            # Get agent instance for verification
            agent_id = AgentId(type=agent.type, key="default")
            agent_instances[name] = await runtime._get_agent(agent_id)

        # Set up expected responses
        moderator_id = AgentId(type=agents["Moderator"].type, key="default")
        expert_id = AgentId(type=agents["Expert"].type, key="default")
        assistant_id = AgentId(type=agents["Assistant"].type, key="default")

        # Configure expected responses
        question_1 = "What are the key benefits of Python?"
        answer_1 = "Python offers readability, extensive libraries, and cross-platform support."
        question_2 = "Can you provide examples of Python's cross-platform support?"
        answer_2 = "Python runs on Windows, macOS, Linux, and many other platforms. You can write once, run anywhere."

        agent_instances["Expert"].expect_response(question_1, answer_1)
        agent_instances["Assistant"].expect_response(question_2, answer_2)

        # Start the group discussion
        messages = [
            (moderator_id, question_1, agents["Expert"].type),
            (expert_id, question_2, agents["Assistant"].type)
        ]

        for sender_id, content, recipient_type in messages:
            message = ChatMessage(
                content=content,
                sender=sender_id.type,  
                recipient=recipient_type
            )
            topic_id = TopicId(type=group_chat_topic, source=sender_id.type)
            print(f"\nPublishing message: {content} from {sender_id.type} to {recipient_type}")
            await runtime.publish_message(message, topic_id, sender=sender_id)
            
            # Give time for message processing
            await asyncio.sleep(1.0)

            # Print message records for debugging
            print("\nMessage Records after sending:", content)
            for name, agent in agent_instances.items():
                print(f"\n{name} received messages:")
                for msg in agent.received_messages:
                    print(f"  From: {msg.sender}, Content: {msg.content}")
                print(f"\n{name} sent messages:")
                for msg in agent.sent_messages:
                    print(f"  To: {msg.recipient}, Content: {msg.content}")

        # Stop the runtime when idle
        await runtime.stop_when_idle()

        # Verify group chat message flow
        # 1. Verify Expert received moderator's question
        assert any(msg.content == question_1 and msg.sender == agents["Moderator"].type 
                  for msg in agent_instances["Expert"].received_messages), \
            "Expert did not receive moderator's question"

        # 2. Verify Expert sent the correct response
        assert any(msg.content == answer_1 
                  for msg in agent_instances["Expert"].sent_messages), \
            "Expert did not send expected response"

        # 3. Verify Assistant received Expert's question
        assert any(msg.content == question_2 and msg.sender == agents["Expert"].type 
                  for msg in agent_instances["Assistant"].received_messages), \
            "Assistant did not receive expert's question"

        # 4. Verify Assistant sent the correct response
        assert any(msg.content == answer_2 
                  for msg in agent_instances["Assistant"].sent_messages), \
            "Assistant did not send expected response"

        # 5. Verify all agents received all messages (group chat functionality)
        for name, agent in agent_instances.items():
            assert len(agent.received_messages) >= 2, \
                f"{name} did not receive all group chat messages"

        # 6. Verify message ordering for all agents
        for name, agent in agent_instances.items():
            for i in range(1, len(agent.received_messages)):
                assert agent.received_messages[i].timestamp >= agent.received_messages[i-1].timestamp, \
                    f"Messages received out of order for {name}"
