#!/usr/bin/env python3
"""Adapter for wake word detector from jarvis_audio."""

import sys
from pathlib import Path


class WakeWordDetector:
    """Wrapper around jarvis_audio.wake_word.WakeWordDetector."""
    
    def __init__(self, model_name: str = "hey_jarvis", threshold: float = 0.6):
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
            
        return True
        
    def check_once(self) -> bool:
        """Check if wake word is currently detected (non-blocking).
        
        Returns:
            True if wake word detected in current audio frame
        """
        # For barge-in, we need a non-blocking check
        # This is a simplified implementation
        import time
        import numpy as np
        
        try:
            if hasattr(self._detector, 'stream') and self._detector.stream:
                # Read one chunk from the stream
                audio_data = self._detector.stream.read(
                    self._detector.chunk_size,
                    exception_on_overflow=False
                )
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Run prediction
                prediction = self._detector.model.predict(audio_array)
                
                # Check if any model exceeded threshold
                for model_name, score in prediction.items():
                    if score >= self._detector.threshold:
                        return True
        except Exception:
            pass
            
        return False
