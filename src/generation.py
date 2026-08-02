"""Text-generation backends used by Avatar.

The default backend keeps the existing Claude CLI behavior.  A deterministic
mock backend is available for offline demos, tests, and contributor setup.
"""

from __future__ import annotations

import os
from typing import Optional, Protocol

from src.claude_cli import call_claude


class GenerationBackend(Protocol):
    """Minimal interface implemented by Avatar text generators."""

    name: str

    def generate(
        self,
        prompt: str,
        timeout: int = 180,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate text for a prompt."""


class ClaudeCLIBackend:
    """Generate text through an authenticated Claude Code CLI process."""

    name = "claude"

    def generate(
        self,
        prompt: str,
        timeout: int = 180,
        system_prompt: Optional[str] = None,
    ) -> str:
        return call_claude(
            prompt,
            timeout=timeout,
            system_prompt=system_prompt,
        )


class MockBackend:
    """Deterministic offline backend for smoke tests and UI exploration.

    It intentionally does not fabricate character-analysis assets.  Preparing
    new profiles, timelines, or behavior rules still requires a capable model.
    """

    name = "mock"

    def generate(
        self,
        prompt: str,
        timeout: int = 180,
        system_prompt: Optional[str] = None,
    ) -> str:
        del timeout

        if system_prompt:
            return (
                "[Offline mock response] The character generation pipeline is "
                "wired correctly. Set AVATAR_GENERATION_BACKEND=claude for a "
                "model-generated reply."
            )

        lowered = prompt.lower()
        if "summarize this conversation" in lowered:
            return (
                '{"summary":"Offline test conversation",'
                '"user_facts":[],"topics":["offline test"]}'
            )
        if "extract the current mental state" in lowered:
            return '{"beliefs":[],"desires":[],"intentions":[]}'
        if "infer:" in lowered and "other_likely_believes" in prompt:
            return (
                '{"other_likely_believes":[],"other_likely_ignorant_of":[],'
                '"communication_adjustment":"", "internal_reasoning":""}'
            )

        raise RuntimeError(
            "The mock backend cannot generate character-analysis assets. "
            "Use AVATAR_GENERATION_BACKEND=claude for asset preparation."
        )


def get_generation_backend(name: Optional[str] = None) -> GenerationBackend:
    """Return a configured backend, defaulting to the Claude CLI adapter."""
    backend_name = (name or os.getenv("AVATAR_GENERATION_BACKEND", "claude"))
    backend_name = backend_name.strip().lower()

    if backend_name == "claude":
        return ClaudeCLIBackend()
    if backend_name == "mock":
        return MockBackend()

    raise ValueError(
        "Unknown generation backend: "
        f"{backend_name}. Available backends: claude, mock"
    )
