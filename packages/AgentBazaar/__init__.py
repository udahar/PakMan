"""
AgentBazaar
Dynamic agent service discovery for the AntiGrav AI ecosystem.

Quick start:
    from AgentBazaar import AgentBazaar

    bazaar = AgentBazaar()

    # Agent side (in each agent's startup)
    bazaar.advertise("validator_1", "ValidatorAgent",
                     skills=["python", "testing", "pytest"])

    # Broker side (when routing a task)
    agent = bazaar.find("pytest")
    if agent:
        print(f"Routing to: {agent['name']} @ {agent.get('endpoint')}")

    # See the full Bazaar state
    print(bazaar.describe())
"""
from .bazaar import AgentBazaar
from .registry import AgentRegistry

__version__ = "0.1.0"
__all__ = ["AgentBazaar", "AgentRegistry"]
