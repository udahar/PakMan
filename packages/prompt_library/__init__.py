# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Frank Prompt Library Module
Parse, index, vet, and match prompts from prompts.chat
Integrates with PromptOS for strategic reasoning
"""

from .parser import PromptParser, create_prompt_parser
from .index import PromptIndex, create_prompt_index
from .vetting import PromptVetter, create_prompt_vetter
from .matcher import PromptMatcher, create_prompt_matcher
from .promptos_integration import PromptOSIntegration, create_promptos_integration
from .strategies import PromptStrategies, PromptStrategy, create_prompt_strategies
from .db_bridge import PromptOSDatabaseBridge, create_prompos_bridge
from .templates import (
    PromptTemplates,
    PromptTemplate,
    create_prompt_templates,
    TemplateEngine,
)
from .analytics import PromptAnalytics, create_prompt_analytics

__all__ = [
    "PromptParser",
    "create_prompt_parser",
    "PromptIndex",
    "create_prompt_index",
    "PromptVetter",
    "create_prompt_vetter",
    "PromptMatcher",
    "create_prompt_matcher",
    "PromptOSIntegration",
    "create_promptos_integration",
    "PromptStrategies",
    "PromptStrategy",
    "create_prompt_strategies",
    "PromptOSDatabaseBridge",
    "create_prompos_bridge",
    "PromptTemplates",
    "PromptTemplate",
    "create_prompt_templates",
    "TemplateEngine",
    "PromptAnalytics",
    "create_prompt_analytics",
]
