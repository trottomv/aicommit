"""Provider factory and exports."""

import json
import os
from pathlib import Path

from providers.anthropic import AnthropicProvider
from providers.google import GoogleProvider
from providers.mistral import MistralProvider
from providers.ollama import OllamaProvider

_PROVIDER_MAP = {
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "mistral": MistralProvider,
    "ollama": OllamaProvider,
}


def load_config(config_path: Path = None) -> dict:
    """Load configuration from JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.json"

    with open(config_path) as f:
        return json.load(f)


def _resolve_base_url(provider_config: dict) -> str:
    """Resolve base URL from provider config."""
    base_url_env = provider_config.get("base_url_env")
    if base_url_env:
        env_url = os.getenv(base_url_env)
        if env_url:
            return env_url

    base_url = provider_config.get("base_url", "")
    if base_url and not base_url.startswith("{"):
        return base_url

    return ""


def get_provider(model_name: str, config_path: Path = None):
    """Get provider instance for given model name."""
    config = load_config(config_path)

    model_config = None
    provider_name = None
    provider_config = None

    for prov_name, prov_conf in config["providers"].items():
        if model_name in prov_conf.get("models", {}):
            model_config = prov_conf["models"][model_name]
            provider_name = prov_name
            provider_config = prov_conf
            break

    if model_config is None:
        available = []
        for prov_conf in config["providers"].values():
            available.extend(prov_conf.get("models", {}).keys())
        raise ValueError(
            f"Unknown model '{model_name}'. Available: {', '.join(available)}"
        )

    provider_class = _PROVIDER_MAP.get(provider_name)
    if provider_class is None:
        raise ValueError(f"Unknown provider '{provider_name}'")

    base_url = _resolve_base_url(provider_config)
    provider = provider_class(model_config["model_id"], base_url)
    provider.validate()
    return provider


def get_default_model(config_path: Path = None) -> str:
    """Get default model from config."""
    config = load_config(config_path)
    return config.get("default_model", "gemini")


def get_prompt_template(config_path: Path = None) -> str | None:
    """Get custom prompt template from config if set."""
    config = load_config(config_path)
    return config.get("prompt_template")
