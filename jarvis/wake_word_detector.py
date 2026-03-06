#!/usr/bin/env python3
"""Adapter for wake word detector from jarvis_audio."""

import sys
from pathlib import Path


class WakeWordDetector:
    """Wrapper around jarvis_audio.wake_word.WakeWordDetector."""
    
    def __init__(self, model_name: str = "hey_jarvis", threshold: float = 0.35):
        """Initialize wake word detector.
        
        Args:
            model_name: Wake word model to use
            threshold: Detection confidence threshold (0-1)
        """
        # Lazy import to avoid requiring dependencies at import time
        sys.path.insert(0, str(Path(__file__).parent.parent / "jarvis_audio"))
        from wake_word import WakeWordDetector as _WakeWordDetector
        
        self._detector = _WakeWordDetector(
            model_name=model_name,
            threshold=threshold
        )
        self._activated = False
        self._barge_in_active = False
        
    def wait_for_activation(self) -> bool:
        """Block until wake word is detected.
        
        Returns:
            True when wake word is detected
        """
        def on_wake():
            self._activated = True
            
        self._activated = False
        self._detector.start_listening(on_wake)
        
        # Wait for activation
        while not self._activated:
            import time
            time.sleep(0.1)

        # Ensure background capture is stopped after activation.
        self._detector.stop_listening()
        self._barge_in_active = False
            
        return True
        
    def check_once(self) -> bool:
        """Check if wake word is currently detected (non-blocking).
        
        Returns:
            True if wake word detected in current audio frame
        """
        # Subprocess-based detector has no direct stream.read API.
        # Start a background listener once per speaking turn and poll the flag.
        try:
            if not self._barge_in_active:
                self._activated = False
                self._detector.start_listening(self._on_barge_in_activation)
                self._barge_in_active = True

            if self._activated:
                self._activated = False
                self._barge_in_active = False
                return True
        except Exception:
            return False

        return False

    def _on_barge_in_activation(self):
        """Internal callback for barge-in polling mode."""
        self._activated = True
