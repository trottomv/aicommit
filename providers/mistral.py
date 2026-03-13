"""Mistral API provider."""

import json
import os
import urllib.request

from providers.base import LLMProvider


class MistralProvider(LLMProvider):
    """Mistral API provider."""

    API_KEY_ENV = "MISTRAL_API_KEY"

    def __init__(self, model_id: str, base_url: str):
        """
        Initialize Mistral API provider.

        Args:
            model_id: The Mistral model ID (e.g., 'mistral-small-latest').
            base_url: The base URL for Mistral API.

        """
        self.model_id = model_id
        self.base_url = base_url
        self.api_key = None

    def validate(self) -> None:
        """Validate that MISTRAL_API_KEY is set."""
        self.api_key = os.getenv(self.API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"{self.API_KEY_ENV} environment variable not set")

    def generate(self, prompt: str) -> str:
        """
        Generate content using Mistral API.

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
        }
        url = f"{self.base_url}/v1/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())

        return self._extract_from_path(data, "choices[0].message.content")
