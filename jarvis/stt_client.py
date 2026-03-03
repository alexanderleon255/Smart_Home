#!/usr/bin/env python3
"""Adapter for Whisper STT from jarvis_audio."""

import sys
from pathlib import Path
import tempfile
import subprocess
import time
import threading
from datetime import datetime, timezone
from typing import Callable, Dict, Any, List, Optional


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
        self._chunks: List[Dict[str, Any]] = []
        self._callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._polling = False
        self._poll_thread: Optional[threading.Thread] = None
        self._poll_interval = 1.0
        self._last_seen_text = ""
        self._lock = threading.Lock()
        self._last_chunk_at: Optional[float] = None
        
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

        self._callback = callback
        self._polling = True
        self._poll_thread = threading.Thread(target=self._poll_transcript_loop, daemon=True)
        self._poll_thread.start()

    def _poll_transcript_loop(self):
        """Poll growing audio recording and emit normalized STT chunks."""
        while self._polling:
            try:
                if self._temp_file and Path(self._temp_file.name).exists():
                    current_text = self._stt.transcribe_file(self._temp_file.name).strip()
                    if current_text and current_text != self._last_seen_text:
                        delta_text = current_text[len(self._last_seen_text):].strip() if current_text.startswith(self._last_seen_text) else current_text
                        self._last_seen_text = current_text

                        chunk = {
                            "timestamp_start": datetime.now(timezone.utc).isoformat(),
                            "timestamp_end": datetime.now(timezone.utc).isoformat(),
                            "text": delta_text,
                            "confidence": 0.0,
                        }

                        with self._lock:
                            self.transcript = current_text
                            self._chunks.append(chunk)
                            self._new_text = True
                            self._last_chunk_at = time.monotonic()

                        if self._callback:
                            try:
                                self._callback(chunk)
                            except Exception:
                                pass
            except Exception:
                pass

            time.sleep(self._poll_interval)
        
    def has_new_text(self) -> bool:
        """Check if new text has been transcribed.
        
        Returns:
            True if new text is available
        """
        with self._lock:
            new_text = self._new_text
            self._new_text = False
            return new_text

    def get_chunks(self) -> List[Dict[str, Any]]:
        """Return normalized STT chunks captured for current utterance."""
        with self._lock:
            return list(self._chunks)

    @property
    def last_chunk_at(self) -> Optional[float]:
        """Return monotonic timestamp of latest STT chunk, if any."""
        with self._lock:
            return self._last_chunk_at
        
    def stop(self):
        """Stop recording and transcribe."""
        self._polling = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2.0)

        if self._recording_process:
            # Stop recording
            self._recording_process.terminate()
            self._recording_process.wait(timeout=2.0)
            
            # Wait a moment for file to be flushed
            time.sleep(0.5)
            
            # Transcribe the recorded audio
            try:
                final_transcript = self._stt.transcribe_file(self._temp_file.name)
                with self._lock:
                    if final_transcript:
                        self.transcript = final_transcript
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
            self._callback = None
