"""
AgentBazaar - bazaar.py
High-level Bazaar API for agents to advertise and discover capabilities.

Usage:
    from AgentBazaar import AgentBazaar

    bazaar = AgentBazaar()

    # Agent registers itself
    bazaar.advertise("coder_1", "CoderAgent", skills=["python", "rust", "code_review"])

    # Broker finds the best agent for a task
    agent = bazaar.find("python")
    print(agent)  # {"agent_id": "coder_1", "name": "CoderAgent", ...}

    # Keep-alive loop (call periodically)
    bazaar.heartbeat("coder_1", status="busy")
"""
from typing import Any, Dict, List, Optional
from .registry import AgentRegistry


class AgentBazaar:
    """
    Central service discovery for the AntiGrav AI ecosystem.

    Agents post capability manifests on startup.
    Brokers query for the most appropriate agent for each task.
    """

    def __init__(self, db_path: str = "agent_bazaar.db"):
        self.registry = AgentRegistry(db_path)

    # ── Agent side ────────────────────────────────────────────────────────────

    def advertise(
        self,
        agent_id: str,
        name: str,
        skills: List[str],
        endpoint: str = "",
        metadata: Dict[str, Any] = None,
    ) -> None:
        """
        Announce this agent's capabilities to the Bazaar.

        Args:
            agent_id: Unique stable ID (e.g., "coder_1").
            name:     Display name (e.g., "CoderAgent").
            skills:   Capability tags (e.g., ["python", "code_review"]).
            endpoint: Optional HTTP URL the agent listens on.
            metadata: Any extra info (version, model, etc.).
        """
        self.registry.register(
            agent_id=agent_id,
            name=name,
            skills=skills,
            endpoint=endpoint,
            metadata=metadata,
            status="idle",
        )
        print(f"[AgentBazaar] '{name}' advertised skills: {skills}")

    def heartbeat(self, agent_id: str, status: str = "idle") -> None:
        """Signal that the agent is still alive."""
        self.registry.heartbeat(agent_id, status)

    def retire(self, agent_id: str) -> None:
        """Remove an agent from the Bazaar."""
        self.registry.deregister(agent_id)

    # ── Broker/consumer side ──────────────────────────────────────────────────

    def find(self, skill: str) -> Optional[dict]:
        """
        Find the best available agent for a skill.

        Returns:
            Agent manifest dict, or None if no agent is available.
        """
        return self.registry.find_best(skill)

    def find_all(self, skill: str) -> List[dict]:
        """Return all available agents for a skill."""
        return self.registry.find_by_skill(skill)

    def list_agents(self) -> List[dict]:
        """List all registered (non-offline) agents."""
        return self.registry.list_all()

    def available_skills(self) -> List[str]:
        """Return all skill tags currently advertised in the Bazaar."""
        return self.registry.all_skills()

    def describe(self) -> dict:
        """Return a summary of the Bazaar state."""
        agents = self.registry.list_all()
        return {
            "agent_count": len(agents),
            "skill_count": len(self.available_skills()),
            "skills": self.available_skills(),
            "agents": [{"id": a["agent_id"], "name": a["name"],
                        "skills": a["skills"], "status": a["status"]}
                       for a in agents],
        }
