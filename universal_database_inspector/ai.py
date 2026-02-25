"""Minimal OpenAI API wrapper.

Provides a single ``prompt_to_model`` function used by the labeler
and describer modules.  Replaces the external ``use_ai`` dependency.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI, BadRequestError

DEFAULT_MODEL_NAME = "gpt-4.1"


def _get_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise EnvironmentError("Missing environment variable: OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def _chat_completion(client: OpenAI, **kwargs) -> object:
    """Call chat completions with automatic parameter fallback.

    Handles two known incompatibilities across model generations:
      - max_tokens -> max_completion_tokens (newer models)
      - temperature not supported (reasoning models like o3-mini)
    """
    try:
        return client.chat.completions.create(**kwargs)
    except BadRequestError as e:
        body = e.body or {}
        param = body.get("param", "") if isinstance(body, dict) else ""

        if param == "max_tokens" and "max_tokens" in kwargs:
            kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
            return _chat_completion(client, **kwargs)

        if param == "temperature" and "temperature" in kwargs:
            del kwargs["temperature"]
            return _chat_completion(client, **kwargs)

        raise


def prompt_to_model(
    prompt: str,
    model_name: str = DEFAULT_MODEL_NAME,
    system_message: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """Send a prompt to an OpenAI model and return the response text."""
    client = _get_client()

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    response = _chat_completion(
        client,
        model=model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content
