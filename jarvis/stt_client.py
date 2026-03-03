#!/usr/bin/env python3
"""Adapter for Whisper STT from jarvis_audio."""

import sys
from pathlib import Path
import tempfile
import subprocess
import time


class WhisperSTT:
    """Wrapper around jarvis_audio.stt.WhisperSTT with streaming support."""
    
    def __init__(self, model_path: str = "models/ggml-small.bin"):
        """Initialize Whisper STT.
        
        Args:
            model_path: Path to Whisper GGML model file
        """
        # Lazy import to avoid requiring dependencies at import time
        sys.path.insert(0, str(Path(__file__).parent.parent / "jarvis_audio"))
        from stt import WhisperSTT as _WhisperSTT
        
        self._stt = _WhisperSTT(model_path=model_path)
        self.transcript = ""
        self._recording_process = None
        self._temp_file = None
        self._new_text = False
        
    def start_streaming(self, callback=None):
        """Start recording audio for transcription.
        
        Args:
            callback: Optional callback for real-time text updates
        """
        # Create temp file for recording
        self._temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self._temp_file.close()
        
        # Start recording
        # Using ffmpeg to record from default microphone
        self._recording_process = subprocess.Popen(
            [
                'ffmpeg',
                '-f', 'avfoundation',  # macOS audio input
                '-i', ':0',  # Default mic
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                self._temp_file.name
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
    def has_new_text(self) -> bool:
        """Check if new text has been transcribed.
        
        Returns:
            True if new text is available
        """
        # Simplified: return False since we do batch transcription
        return False
        
    def stop(self):
        """Stop recording and transcribe."""
        if self._recording_process:
            # Stop recording
            self._recording_process.terminate()
            self._recording_process.wait(timeout=2.0)
            
            # Wait a moment for file to be flushed
            time.sleep(0.5)
            
            # Transcribe the recorded audio
            try:
                self.transcript = self._stt.transcribe_file(self._temp_file.name)
            except Exception as e:
                print(f"Transcription error: {e}")
                self.transcript = ""
            
            # Cleanup
            import os
            try:
                os.unlink(self._temp_file.name)
            except:
                pass
                
            self._recording_process = None
            self._temp_file = None
