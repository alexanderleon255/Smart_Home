"""Wake word detection using openWakeWord with PipeWire audio."""

import os
import subprocess
import struct
import threading
import time
import numpy as np
from typing import Callable, Optional

try:
    from openwakeword.model import Model
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    print("Warning: openWakeWord not installed. Run: pip install openwakeword")


class WakeWordDetector:
    """Detects wake words in audio stream using openWakeWord + PipeWire audio."""
    
    def __init__(
        self,
        model_name: str = "hey_jarvis",
        threshold: float = 0.6,
        sample_rate: int = 16000,
        chunk_size: int = 1280,
        audio_device: str = "jarvis-mic-source",
    ):
        """Initialize wake word detector.
        
        Args:
            model_name: Wake word model to use
            threshold: Detection confidence threshold (0-1)
            sample_rate: Audio sample rate (Hz)
            chunk_size: Audio chunk size (samples)
            audio_device: PipeWire audio device name (e.g., jarvis-mic-source)
        """
        if not OPENWAKEWORD_AVAILABLE:
            raise ImportError("openWakeWord not installed")
        
        self.model_name = model_name
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_device = audio_device
        
        # Load wake word model (openwakeword defaults to built-in models)
        self.model = Model()
        
        # Audio recording process (uses pw-record instead of PyAudio)
        self._record_process: Optional[subprocess.Popen] = None
        self._listen_thread: Optional[threading.Thread] = None
        self._listening = False
        
    def start_listening(self, callback: Callable[[], None]):
        """Start listening for wake word via PipeWire.
        
        Uses pw-record (PipeWire native) instead of PyAudio/JACK.
        
        Args:
            callback: Function to call when wake word detected
        """
        self._listening = True
        self._listen_thread = threading.Thread(
            target=self._listen_loop,
            args=(callback,),
            daemon=True
        )
        self._listen_thread.start()
    
    def _listen_loop(self, callback: Callable[[], None]):
        """Main listening loop using pw-record."""
        try:
            # Start pw-record piped to stdout (raw PCM data)
            # Format: signed 16-bit mono PCM at sample_rate
            cmd = [
                'pw-record',
                '--format=s16',
                '--channels=1',
                f'--rate={self.sample_rate}',
            ]
            
            # Optionally specify output device (if available)
            if self.audio_device:
                cmd.extend(['--target', self.audio_device])
            
            cmd.append('-')  # Output to stdout
            
            self._record_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=self.chunk_size * 2,  # 2 bytes per int16 sample
            )
            
            print(f"🎤 Listening on PipeWire device: {self.audio_device}")
            print(f"   Sample rate: {self.sample_rate} Hz, chunk size: {self.chunk_size}")
            
            # Read chunks of audio data
            byte_size = self.chunk_size * 2  # 2 bytes per int16
            while self._listening and self._record_process:
                try:
                    chunk_bytes = self._record_process.stdout.read(byte_size)
                    if not chunk_bytes:
                        break
                    
                    # Convert bytes to int16 numpy array
                    audio_data = np.frombuffer(chunk_bytes, dtype=np.int16)
                    
                    if len(audio_data) == 0:
                        continue
                    
                    # Get predictions from wake word model
                    predictions = self.model.predict(audio_data)
                    
                    # Check if any wake word detected
                    for word, score in predictions.items():
                        if score >= self.threshold:
                            print(f"✅ Wake word '{word}' detected! Confidence: {score:.2f}")
                            self._listening = False
                            callback()
                            return
                            
                except Exception as e:
                    if self._listening:
                        print(f"⚠️  Audio read error: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Failed to start listening: {e}")
            print(f"   Make sure pw-record is available and {self.audio_device} exists")
        finally:
            self.stop_listening()
    
    def stop_listening(self):
        """Stop listening for wake word."""
        self._listening = False
        if self._record_process:
            try:
                self._record_process.terminate()
                self._record_process.wait(timeout=1)
            except Exception:
                try:
                    self._record_process.kill()
                except Exception:
                    pass
            self._record_process = None
    
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
    
    detector = WakeWordDetector(threshold=0.6)
    detector.start_listening(on_wake_word)
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
        detector.stop_listening()


if __name__ == "__main__":
    main()
