"""Google Gemini API provider."""

import json
import os
import urllib.request

from providers.base import LLMProvider


class GoogleProvider(LLMProvider):
    """Google Gemini API provider."""

    API_KEY_ENV = "GEMINI_API_KEY"

    def __init__(self, model_id: str, base_url: str):
        """
        Initialize Google Gemini provider.

        Args:
            model_id: The Gemini model ID (e.g., 'gemini-2.5-flash').
            base_url: The base URL for Gemini API.

        """
        self.model_id = model_id
        self.base_url = base_url
        self.api_key = None

    def validate(self) -> None:
        """Validate that GEMINI_API_KEY is set."""
        self.api_key = os.getenv(self.API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"{self.API_KEY_ENV} environment variable not set")

    def generate(self, prompt: str) -> str:
        """
        Generate content using Gemini API.

        Args:
            prompt: The text prompt to send to the model.

        Returns:
            Generated text response from the model.

        Raises:
            urllib.error.HTTPError: If API request fails.
            KeyError: If response parsing fails.

        """
        url = (
            f"{self.base_url}/v1beta/models/{self.model_id}"
            f":generateContent?key={self.api_key}"
        )
        body = {"contents": [{"parts": [{"text": prompt}]}]}

        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())

        return self._extract_from_path(data, "candidates[0].content.parts[0].text")
