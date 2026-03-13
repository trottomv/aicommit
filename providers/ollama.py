"""Ollama local API provider."""

import json
import urllib.request

from providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama local API provider."""

    BASE_URL_ENV = "OLLAMA_BASE_URL"

    def __init__(self, model_id: str, base_url: str):
        """
        Initialize Ollama local API provider.

        Args:
            model_id: The Ollama model name (e.g., 'llama3.2').
            base_url: The base URL for Ollama API.

        """
        self.model_id = model_id
        self.base_url = base_url

    def validate(self) -> None:
        """Validate that base URL is set."""
        if not self.base_url:
            raise ValueError("Ollama base URL not set")

    def generate(self, prompt: str) -> str:
        """
        Generate content using Ollama /api/generate endpoint.

        Args:
            prompt: The text prompt to send to the model.

        Returns:
            Generated text response from the model.

        Raises:
            urllib.error.HTTPError: If API request fails.
            KeyError: If response parsing fails.

        """
        url = f"{self.base_url}/api/generate"
        body = {"model": self.model_id, "prompt": prompt, "stream": False}

        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())

        return self._extract_from_path(data, "response")
