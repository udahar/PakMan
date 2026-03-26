"""
SwarmProtocol - broker.py
The central task dispatcher. Routes OFFER messages to capable agents,
waits for results, and handles timeouts/retries.
"""
import time
from typing import Any, Dict, List, Optional
from .bus import SwarmBus
from .models import MessageType, SwarmMessage


class SwarmBroker:
    """
    Routes tasks to registered agents based on skill matching.

    Usage:
        broker = SwarmBroker(bus)
        result = broker.dispatch("python", {"task": "Refactor auth.py"}, timeout=60)
        print(result)  # {"code": "...", "status": "ok"}
    """

    def __init__(self, bus: SwarmBus, broker_id: str = "broker"):
        self.bus = bus
        self.broker_id = broker_id

    def dispatch(
        self,
        skill: str,
        payload: Dict[str, Any],
        timeout: float = 30.0,
        retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """
        Find an agent with the given skill, send an OFFER, and wait for DONE/FAIL.

        Args:
            skill:   Required agent skill (e.g. "python", "research")
            payload: Task details sent to agent
            timeout: Seconds to wait for completion
            retries: Number of retry attempts if no agent accepts

        Returns:
            Agent's result dict on success, None on timeout or all failures.
        """
        for attempt in range(retries + 1):
            agents = self.bus.find_agents_with_skill(skill)
            if not agents:
                time.sleep(0.5)
                continue

            agent_id = agents[0]["agent_id"]
            offer = SwarmMessage(
                sender=self.broker_id,
                recipient=agent_id,
                msg_type=MessageType.OFFER,
                payload=payload,
            )
            self.bus.publish(offer)

            result = self._wait_for_result(offer.id, timeout)
            if result is not None:
                return result

        return None

    def _wait_for_result(
        self, offer_id: str, timeout: float
    ) -> Optional[Dict[str, Any]]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msgs = self.bus.poll(self.broker_id, timeout=0.2)
            for msg in msgs:
                if msg.ref_id != offer_id:
                    continue
                if msg.msg_type == MessageType.DONE:
                    return msg.payload.get("result")
                if msg.msg_type in (MessageType.FAIL, MessageType.REJECT):
                    return None
        return None

    def broadcast(
        self, payload: Dict[str, Any], timeout: float = 5.0
    ) -> List[Dict[str, Any]]:
        """Send an OFFER to all agents and collect all responses."""
        msg = SwarmMessage(
            sender=self.broker_id,
            recipient="broadcast",
            msg_type=MessageType.OFFER,
            payload=payload,
        )
        self.bus.publish(msg)
        time.sleep(timeout)
        results = []
        for reply in self.bus.poll(self.broker_id):
            if reply.ref_id == msg.id and reply.msg_type == MessageType.DONE:
                results.append(reply.payload.get("result", {}))
        return results
