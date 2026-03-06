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
        self._piper_process: Optional[subprocess.Popen] = None
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
            model_path = _resolve_model(self.voice)
            sink = os.environ.get("JARVIS_TTS_SINK", "jarvis-tts-sink")
            ffplay_env = dict(os.environ)
            ffplay_env["PULSE_SINK"] = sink

            self._piper_process = subprocess.Popen(
                [_PIPER_BIN, "--model", model_path, "--output_raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )

            self._process = subprocess.Popen(
                [
                    "ffplay",
                    "-f", "s16le",
                    "-ar", "22050",
                    "-ch_layout", "mono",
                    "-autoexit",
                    "-nodisp",
                    "-",
                ],
                stdin=self._piper_process.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=ffplay_env,
                preexec_fn=os.setsid,
            )

            if self._piper_process.stdout:
                self._piper_process.stdout.close()

            try:
                if self._piper_process.stdin:
                    self._piper_process.stdin.write(text.encode())
                    self._piper_process.stdin.close()
            except BrokenPipeError:
                self.interrupt()
                return False
        
        # Wait for completion
        returncode = self._process.wait()
        if self._piper_process:
            try:
                self._piper_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._piper_process.terminate()
        
        with self._lock:
            interrupted = returncode != 0
            self._process = None
            self._piper_process = None
            return not interrupted
            
    def interrupt(self):
        """Stop current speech immediately."""
        with self._lock:
            pids = [p for p in (self._process, self._piper_process) if p]
            if self._process:
                try:
                    for proc in pids:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except (ProcessLookupError, AttributeError):
                    pass
                finally:
                    self._process = None
                    self._piper_process = None
