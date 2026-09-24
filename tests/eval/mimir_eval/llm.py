"""LLM client used by the harness for generation (naive_direct) and for the judge.

Backends
- ollama: native /api/chat, so num_ctx, temperature and seed are really applied
  (the OpenAI-compatible Ollama endpoint silently ignores num_ctx).
- genai / openai_compat: OpenAI-style /chat/completions (the university GenAI server).
- mock: a Python callable, used by the unit tests.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Callable

import httpx

from .config import PROVIDERS

MockHandler = Callable[[list[dict], dict], str]
_MOCK_HANDLER: MockHandler | None = None


def set_mock_handler(fn: MockHandler | None) -> None:
    global _MOCK_HANDLER
    _MOCK_HANDLER = fn


@dataclass
class LLMResult:
    text: str
    latency_s: float
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    attempts: int = 1
    raw_meta: dict = field(default_factory=dict)


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, provider: str, model: str, temperature: float = 0.0, num_ctx: int = 16384,
                 timeout_s: float = 600, max_retries: int = 2, stream: bool | None = None, **_):
        if provider not in PROVIDERS:
            raise ValueError(f"unknown provider {provider}")
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.stream = (provider == "genai") if stream is None else stream
        spec = PROVIDERS[provider]
        self.base_url = spec["base_url"].rstrip("/")
        self.api_key = os.getenv(spec["api_key_env"]) if spec["api_key_env"] else None
        if provider in ("genai", "openai_compat") and not self.api_key:
            raise LLMError(f"{spec['api_key_env']} is not set (needed for provider '{provider}')")

    @classmethod
    def from_config(cls, cfg: dict) -> "LLMClient":
        return cls(**cfg)

    def describe(self) -> dict:
        return {"provider": self.provider, "model": self.model, "temperature": self.temperature,
                "num_ctx": self.num_ctx}

    # ------------------------------------------------------------------
    def chat(self, messages: list[dict], *, json_mode: bool = True, seed: int | None = None) -> LLMResult:
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            t0 = time.perf_counter()
            try:
                res = self._dispatch(messages, json_mode=json_mode, seed=seed)
                res.latency_s = time.perf_counter() - t0
                res.attempts = attempt
                if not res.text.strip():
                    raise LLMError("empty response")
                return res
            except Exception as e:  # network, HTTP 5xx, empty output
                last_err = e
                time.sleep(min(2 ** attempt, 10))
        raise LLMError(f"{self.provider}/{self.model} failed after retries: {last_err}")

    def _dispatch(self, messages, *, json_mode, seed) -> LLMResult:
        if self.provider == "mock":
            if _MOCK_HANDLER is None:
                raise LLMError("mock provider without handler")
            text = _MOCK_HANDLER(messages, {"model": self.model, "seed": seed, "json_mode": json_mode})
            return LLMResult(text=text, latency_s=0.0, model=self.model)
        if self.provider == "ollama":
            return self._ollama(messages, json_mode, seed)
        return self._openai(messages, json_mode, seed)

    def _ollama(self, messages, json_mode, seed) -> LLMResult:
        base = self.base_url[:-3] if self.base_url.endswith("/v1") else self.base_url
        options = {"temperature": self.temperature, "num_ctx": self.num_ctx}
        if seed is not None:
            options["seed"] = seed
        body = {"model": self.model, "messages": messages, "stream": False, "options": options}
        if json_mode:
            body["format"] = "json"
        with httpx.Client(timeout=self.timeout_s, trust_env=False) as c:
            r = c.post(f"{base}/api/chat", json=body)
            r.raise_for_status()
            data = r.json()
        return LLMResult(
            text=data.get("message", {}).get("content", ""), latency_s=0.0, model=self.model,
            prompt_tokens=data.get("prompt_eval_count"), completion_tokens=data.get("eval_count"),
            raw_meta={k: data.get(k) for k in ("total_duration", "load_duration", "eval_duration")},
        )

    def _openai(self, messages, json_mode, seed) -> LLMResult:
        body: dict = {"model": self.model, "messages": messages, "temperature": self.temperature,
                      "stream": self.stream}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if seed is not None:
            body["seed"] = seed
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/chat/completions"
        with httpx.Client(timeout=self.timeout_s, trust_env=False) as c:
            if not self.stream:
                r = c.post(url, headers=headers, json=body)
                r.raise_for_status()
                data = r.json()
                usage = data.get("usage") or {}
                return LLMResult(text=data["choices"][0]["message"]["content"] or "", latency_s=0.0,
                                 model=data.get("model", self.model),
                                 prompt_tokens=usage.get("prompt_tokens"),
                                 completion_tokens=usage.get("completion_tokens"))
            parts: list[str] = []
            usage: dict = {}
            with c.stream("POST", url, headers=headers, json=body) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    if chunk.get("usage"):
                        usage = chunk["usage"]
                    choices = chunk.get("choices") or [{}]
                    parts.append((choices[0].get("delta") or {}).get("content") or "")
            return LLMResult(text="".join(parts), latency_s=0.0, model=self.model,
                             prompt_tokens=usage.get("prompt_tokens"),
                             completion_tokens=usage.get("completion_tokens"))
