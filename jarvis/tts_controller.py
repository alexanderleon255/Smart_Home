#!/usr/bin/env python3
"""Interruptible TTS controller for Jarvis voice assistant."""

import subprocess
import threading
import signal
import os
from typing import Optional


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
            
            # Start piper → ffplay pipeline
            cmd = (
                f'echo "{safe_text}" | piper --model {self.voice} --output_raw | '
                f'ffplay -f s16le -ar 22050 -ac 1 -autoexit -nodisp - 2>/dev/null'
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
