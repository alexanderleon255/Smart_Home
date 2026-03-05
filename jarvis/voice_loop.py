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
from .service import VoiceServiceManager


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
        model_path: str = "",
        chime_path: Optional[str] = None,
        silence_timeout: float = 2.0,
        max_utterance_seconds: float = 12.0,
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
        self.max_utterance_seconds = max_utterance_seconds
        
        # Session data
        self.user_input: str = ""
        self.response: str = ""
        self._timings = {}

        # Service manager for health reporting
        self._service = VoiceServiceManager()

    def _mark(self, stage: str):
        """Mark stage timestamp for latency metrics."""
        self._timings[stage] = time.monotonic()

    def _print_latency_summary(self):
        """Print key latency metrics for current interaction."""
        if "wake_detected" in self._timings and "tts_start" in self._timings:
            total = self._timings["tts_start"] - self._timings["wake_detected"]
            print(f"⏱️  Wake→TTS start: {total:.2f}s")
        if "stt_start" in self._timings and "stt_end" in self._timings:
            stt = self._timings["stt_end"] - self._timings["stt_start"]
            print(f"⏱️  STT capture: {stt:.2f}s")
        if "llm_start" in self._timings and "llm_end" in self._timings:
            llm = self._timings["llm_end"] - self._timings["llm_start"]
            print(f"⏱️  LLM+broker: {llm:.2f}s")
        
    def start(self):
        """Start the voice loop."""
        print("🎙️  Jarvis voice loop starting...")
        print(f"   State: {self.state.value}")
        print(f"   Chime: {self.chime_path}")
        print()
        self.running = True
        self._service.mark_started()
        
        while self.running:
            try:
                self._service.write_status(self.state.value)
                self._run_iteration()
            except KeyboardInterrupt:
                print("\n👋 Shutting down...")
                self.running = False
            except Exception as e:
                print(f"❌ Error in voice loop: {e}")
                import traceback
                traceback.print_exc()
                self._service.record_error()
                time.sleep(1)  # Prevent tight error loop

        self._service.clear_status()
                
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
            self._timings = {}
            self._mark("wake_detected")
            self._transition_to(VoiceState.ATTENDING)
            
    def _handle_attending(self):
        """Play chime, start STT, collect speech."""
        # Play activation chime
        self._play_chime()
        
        # Start STT
        print("🎤 Listening to user...")
        self._mark("stt_start")
        self.stt.start_streaming(callback=self._on_stt_chunk)

        # Wait until silence timeout after latest chunk, or max utterance duration
        started = time.monotonic()
        last_activity = started
        saw_text = False

        while True:
            now = time.monotonic()
            if self.stt.has_new_text():
                last_activity = now
                saw_text = True

            if saw_text and (now - last_activity) >= self.silence_timeout:
                break

            if (now - started) >= self.max_utterance_seconds:
                break

            time.sleep(0.1)
        
        # Stop STT, get full transcript
        self.stt.stop()
        self._mark("stt_end")
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
        self._mark("llm_start")
        
        try:
            # Call Tool Broker
            result = process_query(self.user_input)
            self.response = result.get("response", "I'm sorry, I couldn't process that.")
            self._mark("llm_end")
            self._service.record_interaction()
            self._transition_to(VoiceState.SPEAKING)
        except Exception as e:
            print(f"❌ Processing error: {e}")
            self.response = "I apologize, I encountered an error."
            self._mark("llm_end")
            self._service.record_error()
            self._transition_to(VoiceState.SPEAKING)
            
    def _handle_speaking(self):
        """Speak response with barge-in monitoring."""
        print(f"🗣️  Jarvis: {self.response}")
        self._mark("tts_start")
        
        # Start barge-in detection
        self.barge_in.start_monitoring()
        
        # Speak (may be interrupted)
        completed = self.tts.speak(self.response)
        
        # Stop barge-in detection and check if interrupted
        was_interrupted = self.barge_in.stop_monitoring()
        
        if completed and not was_interrupted:
            print("✅ Response completed")
            self._print_latency_summary()
            self._transition_to(VoiceState.LISTENING)
        else:
            # Barge-in occurred
            print("🔔 Response interrupted by barge-in")
            self._print_latency_summary()
            self._transition_to(VoiceState.ATTENDING)

    def _on_stt_chunk(self, chunk):
        """Handle normalized STT chunk events."""
        text = (chunk or {}).get("text", "").strip()
        if text:
            print(f"📝 STT chunk: {text}")
            
    def _transition_to(self, new_state: VoiceState):
        """Transition to new state with logging."""
        print(f"🔄 State: {self.state.value} → {new_state.value}")
        print()
        self.state = new_state
        
    def _play_chime(self):
        """Play activation sound (cross-platform)."""
        import sys as _sys
        try:
            if _sys.platform == "darwin":
                cmd = ['afplay', self.chime_path]
            else:
                cmd = ['ffplay', '-nodisp', '-autoexit', self.chime_path]
            subprocess.run(
                cmd,
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
        default="",
        help="Path to Whisper model (auto-detected if empty)"
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
