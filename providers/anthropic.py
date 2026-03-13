"""Anthropic API provider."""

import json
import os
import urllib.request

from providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""

    API_KEY_ENV = "ANTHROPIC_API_KEY"

    def __init__(self, model_id: str, base_url: str):
        """
        Initialize Anthropic API provider.

        Args:
            model_id: The Anthropic model ID (e.g., 'claude-sonnet-4-20250514').
            base_url: The base URL for Anthropic API.

        """
        self.model_id = model_id
        self.base_url = base_url
        self.api_key = None

    def validate(self) -> None:
        """Validate that ANTHROPIC_API_KEY is set."""
        self.api_key = os.getenv(self.API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"{self.API_KEY_ENV} environment variable not set")

    def generate(self, prompt: str) -> str:
        """
        Generate content using Anthropic API.

        Args:
            prompt: The text prompt to send to the model.

        Returns:
            Generated text response from the model.

        Raises:
            urllib.error.HTTPError: If API request fails.
            KeyError: If response parsing fails.

        """
        body = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        }
        url = f"{self.base_url}/v1/messages"
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())

        return self._extract_from_path(data, "content[0].text")
