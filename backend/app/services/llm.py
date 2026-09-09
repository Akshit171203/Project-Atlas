import json
from typing import Protocol

import httpx
from google import genai
from google.genai import types
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.llm_metrics import timed_call


class LLMProvider(Protocol):
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str: ...


class GeminiProvider:
    def __init__(self):
        # max_keepalive_connections=0 avoids httpx.ReadError from reused
        # keep-alive connections getting silently killed between requests
        # in this environment.
        async_client = httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=0)
        )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                httpx_async_client=async_client,
            ),
        )

        self.model = settings.GEMINI_MODEL

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        with timed_call() as call:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "automatic_function_calling": {"disable": True},
                    "max_output_tokens": settings.LLM_MAX_OUTPUT_TOKENS,
                },
            )

            usage = response.usage_metadata
            if usage is not None:
                call["prompt_tokens"] = usage.prompt_token_count
                call["completion_tokens"] = usage.candidates_token_count

            if response.text is None:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text


class OllamaProvider:
    def __init__(self, model_name: str = "llama3.1"):
        # Ollama provides an OpenAI compatible API
        self.client = AsyncOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # required but unused
        )
        self.model = model_name

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        with timed_call() as call:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            )

            if response.usage is not None:
                call["prompt_tokens"] = response.usage.prompt_tokens
                call["completion_tokens"] = response.usage.completion_tokens

            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError(
                    "Ollama returned an empty response."
                )
            return content


def _build_default_llm() -> LLMProvider:
    if settings.LLM_PROVIDER == "ollama":
        return OllamaProvider(model_name=settings.OLLAMA_MODEL)

    if settings.LLM_PROVIDER == "gemini":
        return GeminiProvider()

    raise ValueError(
        f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER!r} "
        "(expected 'gemini' or 'ollama')"
    )


# Controlled by LLM_PROVIDER in .env — no code changes needed to switch.
default_llm: LLMProvider = _build_default_llm()