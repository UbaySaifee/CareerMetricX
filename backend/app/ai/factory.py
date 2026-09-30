"""Factory for instantiating the configured AI Provider."""

from app.ai.base import BaseAIProvider
from app.ai.deterministic import DeterministicFallbackProvider
from app.ai.openai_provider import OpenAICompatibleProvider
from app.core.config import settings
from app.core.logging import logger


def get_ai_provider() -> BaseAIProvider:
    """Return the active intelligence provider according to application settings."""
    provider_type = settings.AI_PROVIDER.lower().strip()

    if provider_type in ["openai", "gemini"]:
        if settings.OPENAI_API_KEY:
            logger.info("Initializing OpenAI/Gemini compatible provider (%s).", settings.AI_MODEL_NAME)
            return OpenAICompatibleProvider()
        else:
            logger.warning("AI_PROVIDER is '%s' but OPENAI_API_KEY is unset. Using deterministic fallback engine.", provider_type)

    # Default to deterministic fallback provider
    return DeterministicFallbackProvider()
