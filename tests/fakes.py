from ff_briefing.llm.seam import LLMError


class FakeLLMClient:
    def __init__(self, response: str = "# Briefing\n", error: LLMError | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def complete(self, context: str, prompt: str) -> str:
        self.calls.append((context, prompt))
        if self.error is not None:
            raise self.error
        return self.response
