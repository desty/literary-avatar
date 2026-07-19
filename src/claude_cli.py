"""Small, tool-free Claude CLI adapter for Avatar's text generation calls."""

import json
import subprocess
from typing import Any, Optional, Type


class ClaudeCLIError(RuntimeError):
    """Raised when the Claude CLI cannot produce a response."""


def parse_json_response(
    response: str,
    expected_type: Optional[Type[Any]] = None,
) -> Any:
    """Extract JSON from plain text or a fenced Claude response."""
    text = response.strip()
    candidates = [text]

    if "```" in text:
        for block in text.split("```")[1::2]:
            candidate = block.strip()
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].lstrip()
            candidates.append(candidate)

    for opening, closing in (("{", "}"), ("[", "]")):
        start = text.find(opening)
        end = text.rfind(closing)
        if start >= 0 and end > start:
            candidates.append(text[start:end + 1])

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if expected_type is not None and not isinstance(data, expected_type):
            continue
        return data

    expected = expected_type.__name__ if expected_type else "JSON value"
    raise ValueError(f"Could not parse {expected} from response: {response[:500]}")


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
