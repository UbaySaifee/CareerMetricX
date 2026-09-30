"""AI and Intelligence package for CareerMetricX."""

from app.ai.base import BaseAIProvider
from app.ai.deterministic import DeterministicFallbackProvider
from app.ai.factory import get_ai_provider
from app.ai.openai_provider import OpenAICompatibleProvider

__all__ = [
    "BaseAIProvider",
    "DeterministicFallbackProvider",
    "OpenAICompatibleProvider",
    "get_ai_provider",
]
