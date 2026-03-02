"""
Configuration management for Tool Broker.

Loads settings from environment variables, with sensible defaults
for local development.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Tool Broker configuration."""
    
    # Ollama settings
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.1:8b"))
    
    # Home Assistant settings
    ha_url: str = field(default_factory=lambda: os.getenv("HA_URL", "http://homeassistant.local:8123"))
    ha_token: Optional[str] = field(default_factory=lambda: _get_ha_token())
    
    # Entity cache settings
    entity_cache_ttl_minutes: int = field(default_factory=lambda: int(os.getenv("ENTITY_CACHE_TTL", "5")))
    
    # LLM settings
    llm_temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    llm_max_retries: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "2")))
    
    # Server settings
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))


def _get_ha_token() -> Optional[str]:
    """
    Retrieve Home Assistant token from secure sources.
    
    Priority:
    1. Environment variable (HA_TOKEN)
    2. macOS Keychain (via keyring)
    3. None (will fail at runtime if HA integration needed)
    """
    # Try environment variable first
    token = os.getenv("HA_TOKEN")
    if token:
        return token
    
    # Try macOS Keychain
    try:
        import keyring
        token = keyring.get_password("home_assistant", "api_token")
        if token:
            return token
    except ImportError:
        pass
    except Exception:
        pass
    
    return None


# Global config instance
config = Config()
