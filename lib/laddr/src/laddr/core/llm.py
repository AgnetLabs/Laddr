"""
LLM backend implementations.

Provides pluggable LLM backends: NoOp (echo), OpenAI, Anthropic, Gemini.
"""

from __future__ import annotations


class NoOpLLM:
    """
    No-op LLM backend that echoes prompts.
    
    Useful for testing and local dev without API keys.
    """

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """Echo the prompt as response."""
        return f"[NoOpLLM Echo] Prompt: {prompt[:100]}..."


class OpenAILLM:
    """OpenAI LLM backend."""

    def __init__(self, api_key: str | None, model: str | None = None, base_url: str | None = None):
        import os
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        # Support per-agent model config via env
        self.default_model = (
            model or os.getenv("AGENT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4"
        )
        self.base_url = base_url
        self._client = None

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """Generate response using OpenAI."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        if self._client is None:
            try:
                import openai
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self._client = openai.AsyncOpenAI(**kwargs)
            except ImportError:
                raise RuntimeError("openai package not installed. Install with: pip install openai")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=kwargs.get("model", self.default_model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )

        return response.choices[0].message.content

    async def generate_with_usage(self, prompt: str, system: str | None = None, **kwargs) -> tuple[str, dict]:
        """Generate response and return (text, usage) with token counts if available."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        if self._client is None:
            try:
                import openai
                client_kwargs = {"api_key": self.api_key}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                self._client = openai.AsyncOpenAI(**client_kwargs)
            except ImportError:
                raise RuntimeError("openai package not installed. Install with: pip install openai")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = await self._client.chat.completions.create(
            model=kwargs.get("model", self.default_model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        text = resp.choices[0].message.content
        usage = {}
        try:
            u = getattr(resp, "usage", None)
            if u:
                usage = {
                    "prompt_tokens": getattr(u, "prompt_tokens", None),
                    "completion_tokens": getattr(u, "completion_tokens", None),
                    "total_tokens": getattr(u, "total_tokens", None),
                    "provider": "openai",
                    "model": kwargs.get("model", self.default_model),
                }
        except Exception:
            usage = {"provider": "openai"}
        return text, usage

    async def generate_batch(self, prompts: list[str], system: str | None = None, **kwargs) -> list[str]:
        # Fallback: run sequentially
        results: list[str] = []
        for p in prompts:
            results.append(await self.generate(p, system=system, **kwargs))
        return results


class AnthropicLLM:
    """Anthropic LLM backend."""

    def __init__(self, api_key: str | None, model: str | None = None):
        import os
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.default_model = model or "claude-3-sonnet-20240229"
        self._client = None

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """Generate response using Anthropic."""
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")

        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed. Install with: pip install anthropic")

        response = await self._client.messages.create(
            model=kwargs.get("model", self.default_model),
            max_tokens=kwargs.get("max_tokens", 1000),
            system=system or "",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def generate_with_usage(self, prompt: str, system: str | None = None, **kwargs) -> tuple[str, dict]:
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed. Install with: pip install anthropic")
        resp = await self._client.messages.create(
            model=kwargs.get("model", self.default_model),
            max_tokens=kwargs.get("max_tokens", 1000),
            system=system or "",
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.content[0].text
        usage = {}
        try:
            u = getattr(resp, "usage", None)
            if u:
                usage = {
                    "prompt_tokens": getattr(u, "input_tokens", None),
                    "completion_tokens": getattr(u, "output_tokens", None),
                    "total_tokens": (getattr(u, "input_tokens", 0) or 0) + (getattr(u, "output_tokens", 0) or 0),
                    "provider": "anthropic",
                    "model": kwargs.get("model", self.default_model),
                }
        except Exception:
            usage = {"provider": "anthropic"}
        return text, usage


class GeminiLLM:
    """Google Gemini LLM backend."""

    def __init__(self, api_key: str | None, model: str | None = None):
        import os
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.default_model = model or "gemini-2.5-flash"
        self._model = None

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """Generate response using Gemini."""
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        if self._model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(kwargs.get("model", self.default_model))
            except ImportError:
                raise RuntimeError("google-generativeai package not installed. Install with: pip install google-generativeai")

        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        response = await self._model.generate_content_async(full_prompt)
        return response.text

    async def generate_with_usage(self, prompt: str, system: str | None = None, **kwargs) -> tuple[str, dict]:
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        if self._model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(kwargs.get("model", self.default_model))
            except ImportError:
                raise RuntimeError("google-generativeai package not installed. Install with: pip install google-generativeai")
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        resp = await self._model.generate_content_async(full_prompt)
        text = getattr(resp, "text", "")
        usage = {}
        try:
            meta = getattr(resp, "usage_metadata", None)
            if meta:
                usage = {
                    "prompt_tokens": getattr(meta, "prompt_token_count", None),
                    "completion_tokens": getattr(meta, "candidates_token_count", None),
                    "total_tokens": getattr(meta, "total_token_count", None),
                    "provider": "gemini",
                    "model": kwargs.get("model", self.default_model),
                }
        except Exception:
            usage = {"provider": "gemini"}
        return text, usage

    async def generate_batch(self, prompts: list[str], system: str | None = None, **kwargs) -> list[str]:
        # Fallback sequentially
        results: list[str] = []
        for p in prompts:
            results.append(await self.generate(p, system=system, **kwargs))
        return results


class GroqLLM:
    """Groq LLM backend (ultra-fast inference)."""

    def __init__(self, api_key: str | None, model: str | None = None):
        import os
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.default_model = model or "llama-3.3-70b-versatile"
        self._client = None

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """Generate response using Groq."""
        if not self.api_key:
            raise ValueError("Groq API key not configured")

        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
            except ImportError:
                raise RuntimeError("openai package not installed. Install with: pip install openai")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=kwargs.get("model", self.default_model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )

        return response.choices[0].message.content

    async def generate_with_usage(self, prompt: str, system: str | None = None, **kwargs) -> tuple[str, dict]:
        """Generate response and return (text, usage) with token counts."""
        if not self.api_key:
            raise ValueError("Groq API key not configured")
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
            except ImportError:
                raise RuntimeError("openai package not installed. Install with: pip install openai")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = await self._client.chat.completions.create(
            model=kwargs.get("model", self.default_model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        text = resp.choices[0].message.content
        usage = {}
        try:
            u = getattr(resp, "usage", None)
            if u:
                usage = {
                    "prompt_tokens": getattr(u, "prompt_tokens", None),
                    "completion_tokens": getattr(u, "completion_tokens", None),
                    "total_tokens": getattr(u, "total_tokens", None),
                    "provider": "groq",
                    "model": kwargs.get("model", self.default_model),
                }
        except Exception:
            usage = {"provider": "groq"}
        return text, usage

    async def generate_batch(self, prompts: list[str], system: str | None = None, **kwargs) -> list[str]:
        results: list[str] = []
        for p in prompts:
            results.append(await self.generate(p, system=system, **kwargs))
        return results


class GrokLLM:
    """xAI Grok LLM backend - uses native HTTP API."""

    def __init__(self, api_key: str | None, model: str | None = None):
        import os
        self.api_key = api_key or os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        self.default_model = model or "grok-4"
        self.base_url = "https://api.x.ai/v1"

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """Generate response using xAI Grok native API."""
        if not self.api_key:
            raise ValueError("xAI API key not configured")

        import json
        try:
            import aiohttp
        except ImportError:
            raise RuntimeError("aiohttp package not installed. Install with: pip install aiohttp")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "model": kwargs.get("model", self.default_model),
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=3600)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"Grok API error ({resp.status}): {error_text}")
                
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def generate_with_usage(self, prompt: str, system: str | None = None, **kwargs) -> tuple[str, dict]:
        """Generate response and return (text, usage) with token counts."""
        if not self.api_key:
            raise ValueError("xAI API key not configured")

        import json
        try:
            import aiohttp
        except ImportError:
            raise RuntimeError("aiohttp package not installed. Install with: pip install aiohttp")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "model": kwargs.get("model", self.default_model),
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=3600)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"Grok API error ({resp.status}): {error_text}")
                
                data = await resp.json()
                text = data["choices"][0]["message"]["content"]
                
                usage = {}
                if "usage" in data:
                    u = data["usage"]
                    usage = {
                        "prompt_tokens": u.get("prompt_tokens"),
                        "completion_tokens": u.get("completion_tokens"),
                        "total_tokens": u.get("total_tokens"),
                        "provider": "grok",
                        "model": kwargs.get("model", self.default_model),
                    }
                else:
                    usage = {"provider": "grok"}
                
                return text, usage

    async def generate_batch(self, prompts: list[str], system: str | None = None, **kwargs) -> list[str]:
        results: list[str] = []
        for p in prompts:
            results.append(await self.generate(p, system=system, **kwargs))
        return results


class HTTPLLM:
    """Generic HTTP LLM adapter expecting a simple JSON API.

    It POSTs to endpoint with body: {"prompt": str, "system": str | null, "params": {...}}
    and expects a JSON response with {"text": str}.
    """

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        import json
        import urllib.error
        import urllib.request
        body = json.dumps({"prompt": prompt, "system": system, "params": kwargs}).encode("utf-8")

        def _do_request():
            req = urllib.request.Request(self.endpoint, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")

        try:
            raw = await asyncio.to_thread(_do_request)  # type: ignore[name-defined]
            data = json.loads(raw)
            return data.get("text", "")
        except Exception as e:  # pragma: no cover - network dependent
            raise RuntimeError(f"HTTP LLM request failed: {e}")

    async def generate_batch(self, prompts: list[str], system: str | None = None, **kwargs) -> list[str]:
        # Fallback: sequential calls
        results: list[str] = []
        for p in prompts:
            results.append(await self.generate(p, system=system, **kwargs))
        return results

    async def generate_with_usage(self, prompt: str, system: str | None = None, **kwargs) -> tuple[str, dict]:
        # Generic HTTP adapter: no standard usage. Return text with empty usage.
        text = await self.generate(prompt, system=system, **kwargs)
        return text, {"provider": "http"}
