"""PromptSKLib — Prompt Skill Library: structured prompting strategies and templates."""

__version__ = "0.1.0"

from .skills.humble_inquiry import humble_inquiry, InquiryResult

__all__ = [
    "humble_inquiry",
    "InquiryResult",
]
