"""
SwarmProtocol - agent.py
Base agent class. Subclass this to create specialized agents.

Example:
    class CoderAgent(BaseSwarmAgent):
        def handle_offer(self, msg):
            code = generate_code(msg.payload["task"])
            return {"code": code, "status": "ok"}

    agent = CoderAgent("coder_1", skills=["python", "code_review"])
    agent.run(bus)  # Blocking worker loop
"""
import threading
import time
from typing import Any, Dict, List, Optional
from .bus import SwarmBus
from .models import AgentCapability, AgentStatus, MessageType, SwarmMessage


class BaseSwarmAgent:
    """
    Base class for all SwarmProtocol agents.

    Subclass and override `handle_offer()` to implement custom logic.
    All other message types (ACCEPT, REJECT, etc.) are handled automatically.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        skills: List[str],
        max_concurrent: int = 1,
        poll_interval: float = 0.5,
    ):
        self.agent_id = agent_id
        self.name = name
        self.skills = skills
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval
        self.status = AgentStatus.IDLE
        self._stop_event = threading.Event()
        self._active_tasks: Dict[str, threading.Thread] = {}

    @property
    def capability(self) -> AgentCapability:
        return AgentCapability(
            agent_id=self.agent_id,
            name=self.name,
            skills=self.skills,
            max_concurrent=self.max_concurrent,
            status=self.status,
        )

    # ── Override this ─────────────────────────────────────────────────────────

    def handle_offer(self, msg: SwarmMessage) -> Optional[Dict[str, Any]]:
        """
        Main task handler. Receives an OFFER message.
        Return a dict (the task result) or raise an exception on failure.
        Return None to REJECT the offer.
        """
        raise NotImplementedError("Subclasses must implement handle_offer()")

    # ── Internal machinery ────────────────────────────────────────────────────

    def run(self, bus: SwarmBus) -> None:
        """Blocking worker loop. Runs until stop() is called."""
        bus.register_agent(self.capability)
        print(f"[{self.name}] Online. Skills: {self.skills}")

        while not self._stop_event.is_set():
            msgs = bus.poll(self.agent_id, timeout=self.poll_interval)
            for msg in msgs:
                if msg.msg_type == MessageType.OFFER:
                    self._handle_offer_async(msg, bus)
            bus.heartbeat(self.agent_id, self.status.value)

    def run_background(self, bus: SwarmBus) -> threading.Thread:
        """Start the agent loop in a background thread."""
        t = threading.Thread(target=self.run, args=(bus,), daemon=True, name=self.name)
        t.start()
        return t

    def stop(self):
        self._stop_event.set()

    def _handle_offer_async(self, msg: SwarmMessage, bus: SwarmBus):
        if len(self._active_tasks) >= self.max_concurrent:
            bus.publish(SwarmMessage(
                sender=self.agent_id,
                recipient=msg.sender,
                msg_type=MessageType.REJECT,
                payload={"reason": "at_capacity"},
                ref_id=msg.id,
            ))
            return

        # Accept first, then execute
        bus.publish(SwarmMessage(
            sender=self.agent_id,
            recipient=msg.sender,
            msg_type=MessageType.ACCEPT,
            payload={"agent": self.name},
            ref_id=msg.id,
        ))
        self.status = AgentStatus.BUSY
        bus.heartbeat(self.agent_id, "busy")

        def execute():
            try:
                result = self.handle_offer(msg)
                if result is None:
                    raise ValueError("handle_offer returned None")
                bus.publish(SwarmMessage(
                    sender=self.agent_id,
                    recipient=msg.sender,
                    msg_type=MessageType.DONE,
                    payload={"result": result},
                    ref_id=msg.id,
                ))
            except Exception as e:
                bus.publish(SwarmMessage(
                    sender=self.agent_id,
                    recipient=msg.sender,
                    msg_type=MessageType.FAIL,
                    payload={"error": str(e)},
                    ref_id=msg.id,
                ))
            finally:
                self._active_tasks.pop(msg.id, None)
                self.status = AgentStatus.IDLE
                bus.heartbeat(self.agent_id, "idle")

        t = threading.Thread(target=execute, daemon=True)
        self._active_tasks[msg.id] = t
        t.start()
