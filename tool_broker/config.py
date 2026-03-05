"""
Configuration management for Tool Broker.

Loads settings from environment variables, with sensible defaults
for local development.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List


def _parse_cors_origins() -> List[str]:
    """Parse comma-separated CORS origins from environment."""
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost,http://127.0.0.1")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass
class Config:
    """Tool Broker configuration."""
    
    # Ollama settings — tiered LLM routing
    # Primary: lightweight model on Pi (always-on, handles simple requests)
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"))
    
    # Sidecar: heavier model on Mac (complex reasoning, may be offline)
    ollama_sidecar_url: str = field(default_factory=lambda: os.getenv("OLLAMA_SIDECAR_URL", ""))
    ollama_sidecar_model: str = field(default_factory=lambda: os.getenv("OLLAMA_SIDECAR_MODEL", "llama3.1:8b"))
    
    # Tiered routing: "auto" | "local" | "sidecar"
    # auto = classify request complexity and route accordingly
    # local = always use local model
    # sidecar = always prefer sidecar (fallback to local if unavailable)
    llm_routing_mode: str = field(default_factory=lambda: os.getenv("LLM_ROUTING_MODE", "auto"))
    
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
    cors_allowed_origins: List[str] = field(default_factory=_parse_cors_origins)
    broker_api_key: Optional[str] = field(default_factory=lambda: os.getenv("TOOL_BROKER_API_KEY"))
    rate_limit_enabled: bool = field(default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true")
    rate_limit_requests: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS", "60")))
    rate_limit_window_seconds: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")))


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
