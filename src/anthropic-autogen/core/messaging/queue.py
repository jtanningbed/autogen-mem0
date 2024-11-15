import asyncio
import logging
from typing import Dict, Set, Optional, AsyncIterator
from collections import defaultdict

from autogen_core.base import AgentId, CancellationToken
from .messages import Message, MessageCategory

class MessageQueue:
    """Asynchronous message queue with routing and delivery tracking"""
    
    def __init__(self):
        self._queues: Dict[AgentId, asyncio.Queue[Message]] = {}
        self._subscriptions: Dict[AgentId, Set[MessageCategory]] = defaultdict(set)
        self._pending_messages: Set[str] = set()
        self._completion_events: Dict[str, asyncio.Event] = {}
        self._logger = logging.getLogger(__name__)

    async def publish(
        self,
        message: Message,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """Publish a message to all subscribed agents"""
        if not message.sender:
            raise ValueError("Message must have a sender")

        self._pending_messages.add(message.id)
        self._completion_events[message.id] = asyncio.Event()

        # Direct message to specific recipient
        if message.recipient:
            await self._deliver_message(message, message.recipient, cancellation_token)
            return

        # Broadcast to all subscribers of this message category
        for agent_id, categories in self._subscriptions.items():
            if message.category in categories:
                await self._deliver_message(message, agent_id, cancellation_token)

    async def _deliver_message(
        self,
        message: Message,
        recipient: AgentId,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """Deliver message to specific recipient"""
        if recipient not in self._queues:
            self._queues[recipient] = asyncio.Queue()

        try:
            if cancellation_token:
                # Create a task for the put operation that can be cancelled
                put_task = asyncio.create_task(self._queues[recipient].put(message))
                cancellation_token.link_future(put_task)
                await put_task
            else:
                await self._queues[recipient].put(message)
            
            self._logger.debug(f"Delivered message {message.id} to {recipient}")
        except asyncio.CancelledError:
            self._logger.info(f"Message delivery cancelled for {message.id}")
            raise

    async def subscribe(
        self,
        agent_id: AgentId,
        categories: Set[MessageCategory]
    ) -> None:
        """Subscribe an agent to receive messages of specific categories"""
        self._subscriptions[agent_id].update(categories)
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()

    async def unsubscribe(
        self,
        agent_id: AgentId,
        categories: Optional[Set[MessageCategory]] = None
    ) -> None:
        """Unsubscribe an agent from message categories"""
        if categories:
            self._subscriptions[agent_id].difference_update(categories)
            if not self._subscriptions[agent_id]:
                del self._subscriptions[agent_id]
        else:
            del self._subscriptions[agent_id]

        # Clean up queue if no more subscriptions
        if agent_id not in self._subscriptions and agent_id in self._queues:
            del self._queues[agent_id]

    async def get_messages(
        self,
        agent_id: AgentId,
        cancellation_token: Optional[CancellationToken] = None
    ) -> AsyncIterator[Message]:
        """Get messages for an agent"""
        if agent_id not in self._queues:
            return

        queue = self._queues[agent_id]
        while True:
            try:
                if cancellation_token:
                    get_task = asyncio.create_task(queue.get())
                    cancellation_token.link_future(get_task)
                    message = await get_task
                else:
                    message = await queue.get()

                yield message
                queue.task_done()
                
                # Mark message as processed
                if message.id in self._pending_messages:
                    self._pending_messages.remove(message.id)
                    if event := self._completion_events.pop(message.id, None):
                        event.set()

            except asyncio.CancelledError:
                self._logger.info(f"Message retrieval cancelled for {agent_id}")
                break

    async def wait_for_completion(
        self,
        message_id: str,
        timeout: Optional[float] = None
    ) -> bool:
        """Wait for a message to be processed"""
        if message_id not in self._completion_events:
            return False

        try:
            await asyncio.wait_for(
                self._completion_events[message_id].wait(),
                timeout
            )
            return True
        except asyncio.TimeoutError:
            return False
