"""
Convenience LLM factory helpers for user-facing API.

Example:
    from laddr.llms import openai, gemini, anthropic, groq, grok
    llm = openai(model="gpt-4o-mini", temperature=0.2)

These return LLM instances compatible with Laddr core and carry
`default_params` that the Agent will pass to generate().
"""
from __future__ import annotations

from typing import Any, Dict

from .core.llm import OpenAILLM, GeminiLLM, AnthropicLLM, GroqLLM, GrokLLM


class _LLMWithDefaults:
    """Wrap an LLM backend with default params for generate()."""

    def __init__(self, backend: Any, default_params: Dict[str, Any] | None = None):
        self._backend = backend
        self.default_params = dict(default_params or {})

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        params = {**self.default_params, **kwargs}
        return await self._backend.generate(prompt, system=system, **params)

    async def generate_with_usage(self, prompt: str, system: str | None = None, **kwargs) -> tuple[str, dict]:
        params = {**self.default_params, **kwargs}
        if hasattr(self._backend, "generate_with_usage"):
            return await self._backend.generate_with_usage(prompt, system=system, **params)  # type: ignore[attr-defined]
        # fallback to text-only
        text = await self._backend.generate(prompt, system=system, **params)
        return text, {}

    # pass-through for batch when supported
    async def generate_batch(self, prompts: list[str], system: str | None = None, **kwargs) -> list[str]:
        params = {**self.default_params, **kwargs}
        if hasattr(self._backend, "generate_batch"):
            return await self._backend.generate_batch(prompts, system=system, **params)  # type: ignore[attr-defined]
        # fallback
        return [await self.generate(p, system=system, **params) for p in prompts]


def openai(model: str | None = None, temperature: float | None = None, base_url: str | None = None) -> _LLMWithDefaults:
    backend = OpenAILLM(api_key=None, model=model, base_url=base_url)
    defaults: Dict[str, Any] = {}
    if temperature is not None:
        defaults["temperature"] = temperature
    if model is not None:
        defaults["model"] = model
    return _LLMWithDefaults(backend, defaults)


def gemini(model: str | None = None, temperature: float | None = None) -> _LLMWithDefaults:
    backend = GeminiLLM(api_key=None, model=model)
    defaults: Dict[str, Any] = {}
    if temperature is not None:
        defaults["temperature"] = temperature
    if model is not None:
        defaults["model"] = model
    return _LLMWithDefaults(backend, defaults)


def anthropic(model: str | None = None, temperature: float | None = None) -> _LLMWithDefaults:
    backend = AnthropicLLM(api_key=None, model=model)
    defaults: Dict[str, Any] = {}
    if temperature is not None:
        defaults["temperature"] = temperature
    if model is not None:
        defaults["model"] = model
    return _LLMWithDefaults(backend, defaults)


def groq(model: str | None = None, temperature: float | None = None) -> _LLMWithDefaults:
    """
    Create a Groq LLM backend instance.
    
    Args:
        model: Model name (default: llama-3.3-70b-versatile)
        temperature: Generation temperature
    
    Example:
        llm = groq(model="llama-3.3-70b-versatile", temperature=0.5)
    """
    backend = GroqLLM(api_key=None, model=model)
    defaults: Dict[str, Any] = {}
    if temperature is not None:
        defaults["temperature"] = temperature
    if model is not None:
        defaults["model"] = model
    return _LLMWithDefaults(backend, defaults)


def grok(model: str | None = None, temperature: float | None = None) -> _LLMWithDefaults:
    """
    Create a xAI Grok LLM backend instance.
    
    Args:
        model: Model name (default: grok-beta)
        temperature: Generation temperature
    
    Example:
        llm = grok(model="grok-beta", temperature=0.7)
    """
    backend = GrokLLM(api_key=None, model=model)
    defaults: Dict[str, Any] = {}
    if temperature is not None:
        defaults["temperature"] = temperature
    if model is not None:
        defaults["model"] = model
    return _LLMWithDefaults(backend, defaults)
