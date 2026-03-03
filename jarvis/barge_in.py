#!/usr/bin/env python3
"""Barge-in detection for voice assistant."""

import threading
import time


class BargeInDetector:
    """Monitors mic input during TTS playback for wake word."""
    
    def __init__(self, wake_word_detector, tts_controller):
        """Initialize barge-in detector.
        
        Args:
            wake_word_detector: WakeWordDetector instance
            tts_controller: InterruptibleTTS instance
        """
        self.wake_word = wake_word_detector
        self.tts = tts_controller
        self._monitoring = False
        self._interrupted = False
        self._thread: threading.Thread = None
        
    def start_monitoring(self):
        """Start listening for barge-in during TTS."""
        self._monitoring = True
        self._interrupted = False
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
    def stop_monitoring(self) -> bool:
        """Stop barge-in detection.
        
        Returns:
            True if barge-in was detected, False otherwise
        """
        self._monitoring = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        return self._interrupted
            
    def _monitor_loop(self):
        """Background loop checking for wake word."""
        while self._monitoring:
            # Check for wake word detection
            if self.wake_word.check_once():
                print("🔔 Barge-in detected!")
                self.tts.interrupt()
                self._interrupted = True
                self._monitoring = False
                return
            time.sleep(0.05)  # 50ms check interval
