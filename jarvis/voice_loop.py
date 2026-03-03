#!/usr/bin/env python3
"""Main voice assistant loop for Jarvis."""

import enum
import time
import subprocess
from typing import Optional
from pathlib import Path

from .wake_word_detector import WakeWordDetector
from .stt_client import WhisperSTT
from .tts_controller import InterruptibleTTS
from .barge_in import BargeInDetector
from .tool_broker_client import process_query


class VoiceState(enum.Enum):
    """Voice loop state machine states."""
    LISTENING = "listening"
    ATTENDING = "attending"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class VoiceLoop:
    """Main voice assistant loop for Jarvis."""
    
    def __init__(
        self,
        model_path: str = "./whisper.cpp/models/ggml-small.en.bin",
        chime_path: Optional[str] = None,
        silence_timeout: float = 2.0
    ):
        """Initialize voice loop.
        
        Args:
            model_path: Path to Whisper model
            chime_path: Path to activation chime sound
            silence_timeout: Seconds of silence before processing
        """
        # Components
        self.wake_word = WakeWordDetector()
        self.stt = WhisperSTT(model_path=model_path)
        self.tts = InterruptibleTTS()
        self.barge_in = BargeInDetector(self.wake_word, self.tts)
        
        # State
        self.state = VoiceState.LISTENING
        self.running = False
        
        # Config
        self.chime_path = chime_path or str(
            Path(__file__).parent.parent / "assets" / "chime.wav"
        )
        self.silence_timeout = silence_timeout
        
        # Session data
        self.user_input: str = ""
        self.response: str = ""
        
    def start(self):
        """Start the voice loop."""
        print("🎙️  Jarvis voice loop starting...")
        print(f"   State: {self.state.value}")
        print(f"   Chime: {self.chime_path}")
        print()
        self.running = True
        
        while self.running:
            try:
                self._run_iteration()
            except KeyboardInterrupt:
                print("\n👋 Shutting down...")
                self.running = False
            except Exception as e:
                print(f"❌ Error in voice loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)  # Prevent tight error loop
                
    def _run_iteration(self):
        """Single iteration of the state machine."""
        
        if self.state == VoiceState.LISTENING:
            self._handle_listening()
            
        elif self.state == VoiceState.ATTENDING:
            self._handle_attending()
            
        elif self.state == VoiceState.PROCESSING:
            self._handle_processing()
            
        elif self.state == VoiceState.SPEAKING:
            self._handle_speaking()
            
    def _handle_listening(self):
        """Wait for wake word."""
        print("👂 Listening for wake word...")
        
        if self.wake_word.wait_for_activation():
            print("✅ Wake word detected!")
            self._transition_to(VoiceState.ATTENDING)
            
    def _handle_attending(self):
        """Play chime, start STT, collect speech."""
        # Play activation chime
        self._play_chime()
        
        # Start STT
        print("🎤 Listening to user...")
        self.stt.start_streaming()
        
        # Wait for silence (end of utterance)
        # Simple approach: fixed duration recording
        time.sleep(self.silence_timeout + 3.0)  # Give user time to speak
        
        # Stop STT, get full transcript
        self.stt.stop()
        self.user_input = self.stt.transcript.strip()
        
        if self.user_input:
            print(f"💬 User said: {self.user_input}")
            self._transition_to(VoiceState.PROCESSING)
        else:
            print("⚠️  No speech detected, returning to listening")
            self._transition_to(VoiceState.LISTENING)
            
    def _handle_processing(self):
        """Send query to Jarvis via Tool Broker."""
        print("🤔 Processing...")
        
        try:
            # Call Tool Broker
            result = process_query(self.user_input)
            self.response = result.get("response", "I'm sorry, I couldn't process that.")
            self._transition_to(VoiceState.SPEAKING)
        except Exception as e:
            print(f"❌ Processing error: {e}")
            self.response = "I apologize, I encountered an error."
            self._transition_to(VoiceState.SPEAKING)
            
    def _handle_speaking(self):
        """Speak response with barge-in monitoring."""
        print(f"🗣️  Jarvis: {self.response}")
        
        # Start barge-in detection
        self.barge_in.start_monitoring()
        
        # Speak (may be interrupted)
        completed = self.tts.speak(self.response)
        
        # Stop barge-in detection and check if interrupted
        was_interrupted = self.barge_in.stop_monitoring()
        
        if completed and not was_interrupted:
            print("✅ Response completed")
            self._transition_to(VoiceState.LISTENING)
        else:
            # Barge-in occurred
            print("🔔 Response interrupted by barge-in")
            self._transition_to(VoiceState.ATTENDING)
            
    def _transition_to(self, new_state: VoiceState):
        """Transition to new state with logging."""
        print(f"🔄 State: {self.state.value} → {new_state.value}")
        print()
        self.state = new_state
        
    def _play_chime(self):
        """Play activation sound."""
        try:
            # Try afplay (macOS)
            subprocess.run(
                ['afplay', self.chime_path],
                check=True,
                timeout=2.0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback: just print
            print("🔔 (chime)")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jarvis Voice Assistant")
    parser.add_argument(
        "--model",
        default="./whisper.cpp/models/ggml-small.en.bin",
        help="Path to Whisper model"
    )
    parser.add_argument(
        "--chime",
        help="Path to activation chime sound"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    loop = VoiceLoop(
        model_path=args.model,
        chime_path=args.chime
    )
    loop.start()


if __name__ == "__main__":
    main()
