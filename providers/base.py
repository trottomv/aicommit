"""Base provider interface for LLM API calls."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def validate(self) -> None:
        """Validate provider configuration (API keys, URLs)."""
        pass

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate content from prompt."""
        pass

    def _extract_from_path(self, data: dict, path: str):
        """Extract value using dot notation: 'candidates[0].content.parts[0].text'."""
        current = data
        for part in path.replace("[", ".").replace("]", "").split("."):
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current[part]
        return current
