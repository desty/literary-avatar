"""Small, tool-free Claude CLI adapter for Avatar's text generation calls."""

import subprocess
from typing import Optional


class ClaudeCLIError(RuntimeError):
    """Raised when the Claude CLI cannot produce a response."""


def call_claude(
    prompt: str,
    timeout: int = 180,
    system_prompt: Optional[str] = None,
) -> str:
    """Run Claude in isolated print mode without coding tools or session state."""
    command = [
        "claude",
        "-p",
        "--safe-mode",
        "--tools",
        "",
        "--no-session-persistence",
        "--effort",
        "low",
        "--output-format",
        "text",
    ]
    if system_prompt:
        command.extend(["--system-prompt", system_prompt])
    command.append(prompt)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClaudeCLIError("Claude CLI timed out") from exc
    except OSError as exc:
        raise ClaudeCLIError("Claude CLI is unavailable") from exc

    if result.returncode != 0:
        detail = result.stderr.strip()[:200] or "unknown error"
        raise ClaudeCLIError(f"Claude CLI failed: {detail}")
    return result.stdout.strip()
