from typing import Protocol

from ff_briefing.errors import BriefingError


class LLMError(BriefingError):
    """The LLM could not produce a briefing; carries the provider's reason."""


class LLMClient(Protocol):
    def complete(self, context: str, prompt: str) -> str: ...
