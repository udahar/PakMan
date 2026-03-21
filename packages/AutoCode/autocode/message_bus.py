"""
Message Bus - Inter-Agent Communication System

Provides async communication between agents with pub/sub patterns.
"""

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from autocode.models import AgentMessage, MessagePriority


@dataclass
class Subscription:
    """Represents a subscription to message topics."""

    agent_name: str
    callback: Callable[[AgentMessage], str]
    topics: list = field(default_factory=list)


class MessageBus:
    """
    Central message routing system for agent communication.

    Features:
    - Direct messaging (agent to agent)
    - Broadcast messaging (one to many)
    - Topic-based subscriptions
    - Message history tracking
    - Priority-based routing
    """

    def __init__(self):
        self.logger = self._setup_logging()
        self._subscriptions: dict[str, list[Subscription]] = defaultdict(list)
        self._agent_callbacks: dict[str, Callable] = {}
        self._message_history: list[AgentMessage] = []
        self._lock = threading.Lock()
        self._max_history = 1000

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("MessageBus")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def register_agent(self, agent_name: str, callback: Callable[[AgentMessage], str]):
        """
        Register an agent to receive messages.

        Args:
            agent_name: Unique name for the agent
            callback: Function to handle incoming messages
        """
        with self._lock:
            self._agent_callbacks[agent_name] = callback
            self.logger.info(f"Agent registered: {agent_name}")

    def unregister_agent(self, agent_name: str):
        """Remove an agent from the message bus."""
        with self._lock:
            if agent_name in self._agent_callbacks:
                del self._agent_callbacks[agent_name]
                self.logger.info(f"Agent unregistered: {agent_name}")

    def subscribe(self, agent_name: str, topic: str, callback: Callable):
        """
        Subscribe an agent to a topic.

        Args:
            agent_name: The subscribing agent
            topic: Topic to subscribe to
            callback: Handler for topic messages
        """
        subscription = Subscription(
            agent_name=agent_name,
            callback=callback,
            topics=[topic],
        )
        with self._lock:
            self._subscriptions[topic].append(subscription)
            self.logger.info(f"Agent {agent_name} subscribed to {topic}")

    def send(self, message: AgentMessage) -> list[str]:
        """
        Send a message to its destination.

        Args:
            message: The message to send

        Returns:
            List of responses from recipients
        """
        with self._lock:
            self._message_history.append(message)
            if len(self._message_history) > self._max_history:
                self._message_history = self._message_history[-self._max_history:]

        self.logger.debug(
            f"Message from {message.from_agent} to {message.to_agent}: "
            f"{message.content[:50]}..."
        )

        responses = []

        if message.to_agent.lower() == "all" or message.to_agent == "*":
            responses.extend(self._broadcast(message))
        elif message.to_agent in self._agent_callbacks:
            response = self._deliver_to_agent(message)
            if response:
                responses.append(response)
        else:
            self.logger.warning(f"Unknown recipient: {message.to_agent}")

        return responses

    def _broadcast(self, message: AgentMessage) -> list[str]:
        """Broadcast message to all registered agents."""
        responses = []
        for agent_name, callback in self._agent_callbacks.items():
            if agent_name != message.from_agent:
                try:
                    response = callback(message)
                    if response:
                        responses.append(response)
                except Exception as e:
                    self.logger.error(
                        f"Error broadcasting to {agent_name}: {e}"
                    )
        return responses

    def _deliver_to_agent(self, message: AgentMessage) -> Optional[str]:
        """Deliver message to a specific agent."""
        callback = self._agent_callbacks.get(message.to_agent)
        if not callback:
            return None

        try:
            return callback(message)
        except Exception as e:
            self.logger.error(f"Error delivering to {message.to_agent}: {e}")
            return None

    def publish_topic(self, topic: str, message: AgentMessage) -> list[str]:
        """
        Publish a message to a topic's subscribers.

        Args:
            topic: The topic to publish to
            message: The message to publish

        Returns:
            List of responses from subscribers
        """
        responses = []
        with self._lock:
            subscribers = self._subscriptions.get(topic, [])

        for subscription in subscribers:
            if subscription.agent_name != message.from_agent:
                try:
                    response = subscription.callback(message)
                    if response:
                        responses.append(response)
                except Exception as e:
                    self.logger.error(
                        f"Error publishing to {subscription.agent_name}: {e}"
                    )

        return responses

    def get_history(
        self,
        thread_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[AgentMessage]:
        """
        Retrieve message history.

        Args:
            thread_id: Optional filter by thread
            limit: Maximum messages to return

        Returns:
            List of messages matching criteria
        """
        with self._lock:
            messages = self._message_history.copy()

        if thread_id:
            messages = [m for m in messages if m.thread_id == thread_id]

        return messages[-limit:]

    def clear_history(self, thread_id: Optional[str] = None):
        """Clear message history, optionally for a specific thread."""
        with self._lock:
            if thread_id:
                self._message_history = [
                    m for m in self._message_history if m.thread_id != thread_id
                ]
            else:
                self._message_history.clear()

        self.logger.info(f"Message history cleared (thread: {thread_id})")

    def get_stats(self) -> dict:
        """Get message bus statistics."""
        with self._lock:
            return {
                "registered_agents": len(self._agent_callbacks),
                "total_subscriptions": sum(
                    len(subs) for subs in self._subscriptions.values()
                ),
                "messages_in_history": len(self._message_history),
                "topics": list(self._subscriptions.keys()),
            }
