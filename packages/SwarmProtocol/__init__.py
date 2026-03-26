"""
SwarmProtocol
Standardized multi-agent negotiation protocol.

Quick start:
    from SwarmProtocol import SwarmBus, SwarmBroker, BaseSwarmAgent

    # 1. Start a shared bus
    bus = SwarmBus("swarm.db")

    # 2. Define a specialized agent
    class CoderAgent(BaseSwarmAgent):
        def handle_offer(self, msg):
            return {"echo": msg.payload}

    agent = CoderAgent("coder_1", "Coder", ["python"])
    agent.run_background(bus)

    # 3. Broker dispatches tasks
    broker = SwarmBroker(bus)
    result = broker.dispatch("python", {"task": "Refactor auth.py"})
    print(result)
"""
from .bus import SwarmBus
from .broker import SwarmBroker
from .agent import BaseSwarmAgent
from .models import SwarmMessage, MessageType, AgentCapability, AgentStatus

__version__ = "0.1.0"
__all__ = [
    "SwarmBus",
    "SwarmBroker",
    "BaseSwarmAgent",
    "SwarmMessage",
    "MessageType",
    "AgentCapability",
    "AgentStatus",
]
