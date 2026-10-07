import subprocess
from pathlib import Path
from typing import Any

import pytest

from ff_briefing.llm.claude_cli import ClaudeCliClient
from ff_briefing.llm.seam import LLMError

REPO_ROOT = Path(__file__).resolve().parents[1]


class RecordingRunner:
    def __init__(self, stdout: str = "# Briefing\n", returncode: int = 0, stderr: str = "") -> None:
        self.result = subprocess.CompletedProcess[str]([], returncode, stdout, stderr)
        self.calls: list[tuple[list[str], dict[str, Any]]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append((argv, kwargs))
        return self.result


def test_api_key_is_removed_from_child_env_and_parent_env_is_untouched() -> None:
    parent = {"ANTHROPIC_API_KEY": "sk-x", "PATH": "/bin"}
    runner = RecordingRunner()

    ClaudeCliClient(runner=runner, environ=parent).complete("ctx", "prompt")

    child_env = runner.calls[0][1]["env"]
    assert "ANTHROPIC_API_KEY" not in child_env
    assert child_env["PATH"] == "/bin"
    assert parent == {"ANTHROPIC_API_KEY": "sk-x", "PATH": "/bin"}


def test_prompt_goes_in_the_print_argument_and_context_via_stdin() -> None:
    runner = RecordingRunner()

    ClaudeCliClient(runner=runner, environ={}).complete("the context", "the prompt")

    argv, kwargs = runner.calls[0]
    assert argv[0] == "claude"
    assert argv[argv.index("-p") + 1] == "the prompt"
    assert kwargs["input"] == "the context"
    assert "the context" not in argv


def test_tools_and_mcp_servers_are_disabled_and_output_is_plain_text() -> None:
    runner = RecordingRunner()

    ClaudeCliClient(runner=runner, environ={}).complete("c", "p")

    argv = runner.calls[0][0]
    assert argv[argv.index("--tools") + 1] == ""
    assert "--strict-mcp-config" in argv
    assert argv[argv.index("--output-format") + 1] == "text"


def test_subprocess_runs_outside_the_repo_so_project_instructions_do_not_leak() -> None:
    runner = RecordingRunner()

    ClaudeCliClient(runner=runner, environ={}).complete("c", "p")

    cwd = Path(runner.calls[0][1]["cwd"]).resolve()
    assert REPO_ROOT not in (cwd, *cwd.parents)


def test_call_is_given_a_timeout_defaulting_to_600_seconds() -> None:
    runner = RecordingRunner()

    ClaudeCliClient(runner=runner, environ={}).complete("c", "p")

    assert runner.calls[0][1]["timeout"] == 600


def test_successful_stdout_is_returned_stripped() -> None:
    runner = RecordingRunner(stdout="\n# Briefing\n\n")

    assert ClaudeCliClient(runner=runner, environ={}).complete("c", "p") == "# Briefing"


def test_nonzero_exit_raises_llm_error_carrying_stderr() -> None:
    runner = RecordingRunner(returncode=1, stderr="not logged in")

    with pytest.raises(LLMError, match="not logged in"):
        ClaudeCliClient(runner=runner, environ={}).complete("c", "p")


def test_missing_claude_binary_raises_llm_error() -> None:
    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("claude")

    with pytest.raises(LLMError, match="claude"):
        ClaudeCliClient(runner=runner, environ={}).complete("c", "p")


def test_timeout_raises_llm_error() -> None:
    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(argv, 600)

    with pytest.raises(LLMError, match="timed out"):
        ClaudeCliClient(runner=runner, environ={}).complete("c", "p")


def test_whitespace_only_output_raises_llm_error_instead_of_returning_empty_text() -> None:
    runner = RecordingRunner(stdout=" \n\t ")

    with pytest.raises(LLMError, match="empty"):
        ClaudeCliClient(runner=runner, environ={}).complete("c", "p")
