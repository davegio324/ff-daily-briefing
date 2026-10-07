import os
import subprocess
import tempfile
from collections.abc import Callable, Mapping

from ff_briefing.llm.seam import LLMError

Runner = Callable[..., subprocess.CompletedProcess[str]]

DEFAULT_TIMEOUT_SECONDS = 600


class ClaudeCliClient:
    """Runs headless `claude -p` on the user's subscription."""

    def __init__(
        self,
        runner: Runner = subprocess.run,
        environ: Mapping[str, str] | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._runner = runner
        self._environ = os.environ if environ is None else environ
        self._timeout = timeout

    def complete(self, context: str, prompt: str) -> str:
        # An API key in the child would switch `claude` from subscription to API billing.
        env = {k: v for k, v in self._environ.items() if k != "ANTHROPIC_API_KEY"}
        argv = [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "text",
            "--tools",
            "",
            "--strict-mcp-config",
        ]
        # Neutral cwd keeps this repo's CLAUDE.md and settings out of the briefing call.
        with tempfile.TemporaryDirectory() as cwd:
            try:
                result = self._runner(
                    argv,
                    input=context,
                    env=env,
                    cwd=cwd,
                    timeout=self._timeout,
                    capture_output=True,
                    text=True,
                )
            except FileNotFoundError as exc:
                raise LLMError(f"claude binary not found: {exc}") from exc
            except subprocess.TimeoutExpired as exc:
                raise LLMError(f"claude timed out after {self._timeout}s") from exc
        if result.returncode != 0:
            raise LLMError(f"claude exited {result.returncode}: {result.stderr.strip()}")
        text = result.stdout.strip()
        if not text:
            raise LLMError("claude returned empty output")
        return text
