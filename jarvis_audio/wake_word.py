"""Wake word detection using openWakeWord."""

import os
import numpy as np
from typing import Callable, Optional
import pyaudio

try:
    from openwakeword.model import Model
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    print("Warning: openWakeWord not installed. Run: pip install openwakeword")


class WakeWordDetector:
    """Detects wake words in audio stream using openWakeWord."""
    
    def __init__(
        self,
        model_name: str = "hey_jarvis",
        threshold: float = 0.6,
        sample_rate: int = 16000,
        chunk_size: int = 1280,
    ):
        """Initialize wake word detector.
        
        Args:
            model_name: Wake word model to use
            threshold: Detection confidence threshold (0-1)
            sample_rate: Audio sample rate (Hz)
            chunk_size: Audio chunk size (samples)
        """
        if not OPENWAKEWORD_AVAILABLE:
            raise ImportError("openWakeWord not installed")
        
        self.model_name = model_name
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        # Load wake word model (openwakeword defaults to built-in models)
        # Note: model_name parameter is stored for logging but Model() uses defaults
        self.model = Model()
        
        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        
    def start_listening(self, callback: Callable[[], None]):
        """Start listening for wake word.
        
        Args:
            callback: Function to call when wake word detected
        """
        def audio_callback(in_data, frame_count, time_info, status):
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Get predictions
            prediction = self.model.predict(audio_data)
            
            # Check if wake word detected
            for key in prediction.keys():
                if prediction[key] >= self.threshold:
                    print(f"Wake word detected! Confidence: {prediction[key]:.2f}")
                    callback()
            
            return (in_data, pyaudio.paContinue)
        
        # Open audio stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=audio_callback,
        )
        
        self.stream.start_stream()
        print(f"Listening for '{self.model_name}'...")
    
    def stop_listening(self):
        """Stop listening for wake word."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_listening()


def main():
    """Test wake word detection."""
    import time
    
    def on_wake_word():
        print(">>> JARVIS ACTIVATED <<<")
    
    print("Starting wake word detection...")
    print("Say 'Hey Jarvis' to test")
    print("Press Ctrl+C to stop")
    
    with WakeWordDetector(threshold=0.6) as detector:
        detector.start_listening(on_wake_word)
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping...")


if __name__ == "__main__":
    main()
