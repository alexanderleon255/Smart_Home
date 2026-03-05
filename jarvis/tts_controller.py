#!/usr/bin/env python3
"""Interruptible TTS controller for Jarvis voice assistant."""

import subprocess
import threading
import signal
import os
from pathlib import Path
from typing import Optional

# Resolve Piper paths (same defaults as jarvis_audio.tts)
_HOME = Path.home()
_PIPER_BIN = os.environ.get(
    "PIPER_PATH",
    str(_HOME / ".local" / "piper" / "piper" / "piper"),
)
_PIPER_MODEL_DIR = os.environ.get(
    "PIPER_MODEL_DIR",
    str(_HOME / ".local" / "piper" / "models"),
)


def _resolve_model(voice: str) -> str:
    """Resolve a voice name to a full .onnx model path if needed."""
    if Path(voice).exists():
        return voice
    candidate = Path(_PIPER_MODEL_DIR) / f"{voice}.onnx"
    if candidate.exists():
        return str(candidate)
    return voice  # fallback


class InterruptibleTTS:
    """TTS that can be interrupted mid-speech."""
    
    def __init__(self, voice: str = "en_US-lessac-medium"):
        """Initialize TTS controller.
        
        Args:
            voice: Piper voice model to use
        """
        self.voice = voice
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        
    def speak(self, text: str) -> bool:
        """
        Speak text, returns True if completed, False if interrupted.
        
        Args:
            text: Text to speak
            
        Returns:
            True if speech completed, False if interrupted
        """
        with self._lock:
            # Escape quotes in text
            safe_text = text.replace('"', '\\"')
            
            # Start piper → paplay pipeline (resolved paths)
            # Route TTS audio to the jarvis-tts-sink virtual device so
            # SonoBus can pick it up and relay to AirPods.
            model_path = _resolve_model(self.voice)
            sink = os.environ.get("JARVIS_TTS_SINK", "jarvis-tts-sink")
            cmd = (
                f'echo "{safe_text}" | {_PIPER_BIN} --model {model_path} --output_raw | '
                f'PULSE_SINK={sink} ffplay -f s16le -ar 22050 -ch_layout mono '
                f'-autoexit -nodisp - 2>/dev/null'
            )
            
            self._process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group for clean kill
            )
        
        # Wait for completion
        returncode = self._process.wait()
        
        with self._lock:
            interrupted = returncode != 0
            self._process = None
            return not interrupted
            
    def interrupt(self):
        """Stop current speech immediately."""
        with self._lock:
            if self._process:
                try:
                    # Kill entire process group to stop all pipeline components
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                except (ProcessLookupError, AttributeError):
                    pass  # Process already terminated
                finally:
                    self._process = None
