"""Configuration for Autonomous Secretary."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SecretaryConfig:
    """Configuration for secretary pipeline."""
    
    # Audio/Transcription settings
    whisper_model: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "base.en"))
    transcription_chunk_seconds: int = field(default_factory=lambda: int(os.getenv("TRANSCRIPTION_CHUNK_SECONDS", "2")))
    
    # Secretary engine settings
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.1:8b"))
    secretary_update_interval_seconds: int = field(default_factory=lambda: int(os.getenv("SECRETARY_UPDATE_INTERVAL", "25")))
    
    # Session settings
    session_base_dir: Path = field(default_factory=lambda: Path(os.getenv("SESSION_BASE_DIR", "/hub_sessions")))
    max_session_retention_days: int = field(default_factory=lambda: int(os.getenv("MAX_SESSION_RETENTION_DAYS", "365")))
    
    # Processing settings
    enable_speaker_diarization: bool = field(default_factory=lambda: os.getenv("ENABLE_SPEAKER_DIARIZATION", "false").lower() == "true")
    high_accuracy_model: str = field(default_factory=lambda: os.getenv("HIGH_ACCURACY_MODEL", "small.en"))
    
    # Output paths (relative to session directory)
    transcript_live_file: str = "transcript_live.txt"
    transcript_final_file: str = "transcript_final.txt"
    notes_live_file: str = "notes_live.md"
    notes_final_file: str = "notes_final.md"
    memory_update_file: str = "memory_update.json"
    raw_audio_file: str = "raw_audio.wav"


# Global config instance
secretary_config = SecretaryConfig()
