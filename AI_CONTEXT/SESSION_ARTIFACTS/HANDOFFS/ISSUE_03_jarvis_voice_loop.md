# [Background Agent] Issue #3: Jarvis Voice Loop + Barge-in

**Roadmap Items:** P6-08, P6-09, P6-10  
**Estimated Effort:** 6-8h total  
**Estimated LOC:** ~200  
**Priority:** HIGH (completes voice interface)  
**Dependencies:** Issue #1 (Tool Broker) AND Issue #2 (Audio Components)  
**Parallel Track:** WAVE 2 — Start after Issues #1 and #2 complete

---

## 🎯 Objective

Integrate all audio components from Issue #2 into a cohesive voice loop with barge-in capability. The loop should: detect wake word → start STT → send to Jarvis → TTS response → allow interruption → return to listening.

---

## 📚 Context to Load

**Required Reading:**
- `Smart_Home/AI_CONTEXT/SOURCES/vision_document.md` — §5.4 (Real-Time Voice Architecture)
- `Smart_Home/References/Jarvis_Assistant_Architecture_v2.0.md` — Voice loop spec
- `Smart_Home/References/Explicit_Interface_Contracts_v1.0.md` — §3 (Voice Pipeline: barge-in rules, STT/TTS schemas)

**Required Code (from Issue #1):**
- `Smart_Home/tool_broker/main.py` — `process_query()` function for LLM calls

**Required Code (from Issue #2):**
- `Smart_Home/jarvis/wake_word_detector.py`
- `Smart_Home/jarvis/stt_client.py`
- `Smart_Home/jarvis/tts_client.py`
- `Smart_Home/Modelfile`

**Why WAVE 2:** This issue imports from BOTH Issue #1 (Tool Broker) and Issue #2 (Audio). Both must complete before this can start.

**Architecture:**
```
            ┌─────────────────────────────────────────────┐
            │                 VOICE LOOP                  │
            └─────────────────────────────────────────────┘
                         ┌─────────────────┐
                         │   LISTENING     │ ←── Wake word detector active
                         │  (idle state)   │
                         └────────┬────────┘
                                  │ "Hey Jarvis" detected
                                  ▼
                         ┌─────────────────┐
                         │   ATTENDING     │ ←── Chime plays, STT starts
                         │ (user speaking) │
                         └────────┬────────┘
                                  │ Speech ends (silence detection)
                                  ▼
                         ┌─────────────────┐
                         │  PROCESSING     │ ←── Query sent to Jarvis
                         │   (LLM call)    │
                         └────────┬────────┘
                                  │ Response received
                                  ▼
                         ┌─────────────────┐
                         │   SPEAKING      │ ←── TTS playing
                         │ (Jarvis reply)  │
                         └────────┬────────┘
                    ┌─────────────┴─────────────┐
                    │                           │
            "Hey Jarvis"                  Speech ends
           (barge-in)                          │
                    │                           │
                    ▼                           ▼
           Back to ATTENDING          Back to LISTENING
```

---

## 📋 Detailed Tasks

### P6-08: Barge-in Capability — 2h

**Goal:** Allow user to interrupt Jarvis mid-speech by saying wake word

**Barge-in Logic:**
```python
#!/usr/bin/env python3
# barge_in.py

import threading
import time

class BargeInDetector:
    """Monitors mic input during TTS playback for wake word."""
    
    def __init__(self, wake_word_detector, tts_controller):
        self.wake_word = wake_word_detector
        self.tts = tts_controller
        self._monitoring = False
        self._thread = None
        
    def start_monitoring(self):
        """Start listening for barge-in during TTS."""
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop)
        self._thread.start()
        
    def stop_monitoring(self):
        """Stop barge-in detection."""
        self._monitoring = False
        if self._thread:
            self._thread.join()
            
    def _monitor_loop(self):
        """Background loop checking for wake word."""
        while self._monitoring:
            if self.wake_word.check_once():
                print("Barge-in detected!")
                self.tts.interrupt()
                self._monitoring = False
                # Signal to main loop: go to ATTENDING state
                return True
            time.sleep(0.05)  # 50ms check interval
        return False
```

**TTS Controller with Interruption:**
```python
#!/usr/bin/env python3
# tts_controller.py

import subprocess
import threading
import signal

class InterruptibleTTS:
    """TTS that can be interrupted mid-speech."""
    
    def __init__(self, voice: str = "en_US-lessac-medium"):
        self.voice = voice
        self._process = None
        self._lock = threading.Lock()
        
    def speak(self, text: str) -> bool:
        """
        Speak text, returns True if completed, False if interrupted.
        """
        with self._lock:
            # Start piper → ffplay pipeline
            cmd = f'echo "{text}" | piper --model {self.voice} --output_raw | ' \
                  f'ffplay -f s16le -ar 22050 -ac 1 -autoexit -nodisp -'
            
            self._process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
            )
        
        # Wait for completion
        self._process.wait()
        
        with self._lock:
            interrupted = self._process.returncode != 0
            self._process = None
            return not interrupted
            
    def interrupt(self):
        """Stop current speech immediately."""
        with self._lock:
            if self._process:
                self._process.terminate()
                # Also kill child processes
                try:
                    subprocess.run(['pkill', '-P', str(self._process.pid)])
                except:
                    pass
```

**Acceptance Criteria:**
- [ ] TTS can be stopped mid-utterance
- [ ] Wake word detection works during TTS
- [ ] Barge-in triggers state change to ATTENDING
- [ ] Audio pipeline cleanly recovers

---

### P6-09: Voice Loop Integration — 3h

**Goal:** Unified state machine connecting all components

**Voice Loop Implementation:**
```python
#!/usr/bin/env python3
# voice_loop.py

import enum
import time
import subprocess
from typing import Optional

from wake_word_detector import WakeWordDetector
from stt_client import WhisperSTT
from tts_controller import InterruptibleTTS
from barge_in import BargeInDetector
from tool_broker.main import process_query  # From Issue #1

class VoiceState(enum.Enum):
    LISTENING = "listening"
    ATTENDING = "attending"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    
class VoiceLoop:
    """Main voice assistant loop for Jarvis."""
    
    def __init__(self):
        # Components
        self.wake_word = WakeWordDetector()
        self.stt = WhisperSTT(model_path="./whisper.cpp/models/ggml-small.en.bin")
        self.tts = InterruptibleTTS()
        self.barge_in = BargeInDetector(self.wake_word, self.tts)
        
        # State
        self.state = VoiceState.LISTENING
        self.running = False
        
        # Config
        self.chime_path = "~/Developer/BoltPatternSuiteV.1/Smart_Home/assets/chime.wav"
        self.silence_timeout = 2.0  # seconds of silence before processing
        
    def start(self):
        """Start the voice loop."""
        print("Jarvis voice loop starting...")
        self.running = True
        
        while self.running:
            try:
                self._run_iteration()
            except KeyboardInterrupt:
                print("\nShutting down...")
                self.running = False
            except Exception as e:
                print(f"Error in voice loop: {e}")
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
        print("Listening for wake word...")
        
        if self.wake_word.wait_for_activation():
            print("Wake word detected!")
            self._transition_to(VoiceState.ATTENDING)
            
    def _handle_attending(self):
        """Play chime, start STT, collect speech."""
        # Play activation chime
        self._play_chime()
        
        # Start STT
        print("Listening to user...")
        self.stt.start_streaming(callback=lambda text: print(f"  [{text}]"))
        
        # Wait for silence (end of utterance)
        last_speech = time.time()
        while time.time() - last_speech < self.silence_timeout:
            if self.stt.has_new_text():
                last_speech = time.time()
            time.sleep(0.1)
            
        # Stop STT, get full transcript
        self.stt.stop()
        self.user_input = self.stt.transcript.strip()
        
        if self.user_input:
            print(f"User said: {self.user_input}")
            self._transition_to(VoiceState.PROCESSING)
        else:
            print("No speech detected, returning to listening")
            self._transition_to(VoiceState.LISTENING)
            
    def _handle_processing(self):
        """Send query to Jarvis via Tool Broker."""
        print("Processing...")
        
        try:
            # Call Tool Broker (from Issue #1)
            result = process_query(self.user_input)
            self.response = result.get("response", "I'm sorry, I couldn't process that.")
            self._transition_to(VoiceState.SPEAKING)
        except Exception as e:
            print(f"Processing error: {e}")
            self.response = "I apologize, I encountered an error."
            self._transition_to(VoiceState.SPEAKING)
            
    def _handle_speaking(self):
        """Speak response with barge-in monitoring."""
        print(f"Jarvis: {self.response}")
        
        # Start barge-in detection
        self.barge_in.start_monitoring()
        
        # Speak (may be interrupted)
        completed = self.tts.speak(self.response)
        
        # Stop barge-in detection
        self.barge_in.stop_monitoring()
        
        if completed:
            self._transition_to(VoiceState.LISTENING)
        else:
            # Barge-in occurred
            print("Response interrupted")
            self._transition_to(VoiceState.ATTENDING)
            
    def _transition_to(self, new_state: VoiceState):
        """Transition to new state with logging."""
        print(f"State: {self.state.value} → {new_state.value}")
        self.state = new_state
        
    def _play_chime(self):
        """Play activation sound."""
        try:
            subprocess.run(['afplay', self.chime_path], check=True)
        except:
            print("(chime)")  # Fallback if no sound file


if __name__ == "__main__":
    loop = VoiceLoop()
    loop.start()
```

**Recording Integration:**
```python
# Add to voice_loop.py - recording per session

class VoiceLoop:
    def __init__(self):
        # ... existing init ...
        self.recording_process = None
        
    def _start_session_recording(self):
        """Start recording when wake word detected."""
        import subprocess
        from datetime import datetime
        
        session_dir = datetime.now().strftime(
            "~/hub_sessions/%Y/%m/%d/session_%Y%m%d_%H%M%S"
        )
        subprocess.run(['mkdir', '-p', session_dir], check=True)
        
        self.recording_process = subprocess.Popen([
            'ffmpeg', '-f', 'avfoundation', '-i', ':BlackHole 2ch',
            '-ar', '16000', '-ac', '1',
            f'{session_dir}/raw_audio.wav'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    def _stop_session_recording(self):
        """Stop recording when conversation ends."""
        if self.recording_process:
            self.recording_process.terminate()
            self.recording_process = None
```

**Acceptance Criteria:**
- [ ] State machine cycles correctly through all states
- [ ] Wake word triggers LISTENING → ATTENDING
- [ ] Silence detection triggers ATTENDING → PROCESSING  
- [ ] LLM response triggers PROCESSING → SPEAKING
- [ ] TTS completion triggers SPEAKING → LISTENING
- [ ] Barge-in triggers SPEAKING → ATTENDING
- [ ] Recording captures full sessions

---

### P6-10: Voice Loop Testing — 2h

**Goal:** Comprehensive tests for voice loop behavior

**Test Suite:**
```python
#!/usr/bin/env python3
# test_voice_loop.py

import pytest
import time
from unittest.mock import Mock, patch

from voice_loop import VoiceLoop, VoiceState


class TestStateTransitions:
    """Test state machine transitions."""
    
    def setup_method(self):
        self.loop = VoiceLoop()
        
    def test_initial_state_is_listening(self):
        assert self.loop.state == VoiceState.LISTENING
        
    def test_wake_word_transitions_to_attending(self):
        self.loop.wake_word = Mock()
        self.loop.wake_word.wait_for_activation.return_value = True
        
        self.loop._handle_listening()
        
        assert self.loop.state == VoiceState.ATTENDING
        
    def test_speech_transitions_to_processing(self):
        self.loop.stt = Mock()
        self.loop.stt.transcript = "Turn on the light"
        self.loop.stt.has_new_text.return_value = False
        
        self.loop._handle_attending()
        
        assert self.loop.state == VoiceState.PROCESSING
        assert self.loop.user_input == "Turn on the light"
        
    def test_empty_speech_returns_to_listening(self):
        self.loop.stt = Mock()
        self.loop.stt.transcript = ""
        self.loop.stt.has_new_text.return_value = False
        
        self.loop._handle_attending()
        
        assert self.loop.state == VoiceState.LISTENING


class TestBargeIn:
    """Test barge-in interrupt functionality."""
    
    def test_barge_in_interrupts_speech(self):
        loop = VoiceLoop()
        loop.tts = Mock()
        loop.tts.speak.return_value = False  # Simulates interruption
        loop.barge_in = Mock()
        
        loop.state = VoiceState.SPEAKING
        loop.response = "This is a test"
        loop._handle_speaking()
        
        assert loop.state == VoiceState.ATTENDING
        
    def test_completed_speech_returns_to_listening(self):
        loop = VoiceLoop()
        loop.tts = Mock()
        loop.tts.speak.return_value = True  # Completed
        loop.barge_in = Mock()
        
        loop.state = VoiceState.SPEAKING
        loop.response = "Test"
        loop._handle_speaking()
        
        assert loop.state == VoiceState.LISTENING


class TestToolBrokerIntegration:
    """Test integration with Tool Broker."""
    
    @patch('voice_loop.process_query')
    def test_processing_calls_tool_broker(self, mock_process):
        mock_process.return_value = {"response": "Done!"}
        
        loop = VoiceLoop()
        loop.user_input = "Turn on the kitchen light"
        loop._handle_processing()
        
        mock_process.assert_called_once_with("Turn on the kitchen light")
        assert loop.response == "Done!"
        assert loop.state == VoiceState.SPEAKING
        
    @patch('voice_loop.process_query')
    def test_processing_handles_error(self, mock_process):
        mock_process.side_effect = Exception("API Error")
        
        loop = VoiceLoop()
        loop.user_input = "Test"
        loop._handle_processing()
        
        assert "apologize" in loop.response.lower()
        assert loop.state == VoiceState.SPEAKING


class TestEndToEnd:
    """End-to-end integration tests (require hardware)."""
    
    @pytest.mark.skip(reason="Requires audio hardware")
    def test_full_interaction_cycle(self):
        """Test complete wake -> speak -> respond -> idle cycle."""
        loop = VoiceLoop()
        
        # Simulate wake word
        loop._transition_to(VoiceState.ATTENDING)
        
        # Simulate speech
        loop.stt = Mock()
        loop.stt.transcript = "What time is it?"
        loop.stt.has_new_text.return_value = False
        loop._handle_attending()
        
        # Process
        loop._handle_processing()
        
        # Speak
        loop.tts = Mock()
        loop.tts.speak.return_value = True
        loop.barge_in = Mock()
        loop._handle_speaking()
        
        assert loop.state == VoiceState.LISTENING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Manual Test Script:**
```bash
#!/bin/bash
# manual_voice_test.sh

echo "=== Manual Voice Loop Testing ==="
echo ""
echo "This script guides you through manual testing."
echo ""

# Test 1: Wake word
echo "TEST 1: Wake Word"
echo "  - Say 'Hey Jarvis' clearly"
echo "  - Expected: Chime sound, state → ATTENDING"
echo "  Press Enter when ready..."
read

# Test 2: Basic command
echo "TEST 2: Basic Command"
echo "  - Say 'Hey Jarvis' then 'What time is it?'"
echo "  - Expected: Time response via TTS"
echo "  Press Enter when ready..."
read

# Test 3: Device control
echo "TEST 3: Device Control"
echo "  - Say 'Hey Jarvis' then 'Turn on the living room light'"
echo "  - Expected: Tool call executed, confirmation TTS"
echo "  Press Enter when ready..."
read

# Test 4: Barge-in
echo "TEST 4: Barge-in"
echo "  - Trigger a long response, then say 'Hey Jarvis' mid-speech"
echo "  - Expected: TTS stops, state → ATTENDING immediately"
echo "  Press Enter when ready..."
read

# Test 5: Silence handling
echo "TEST 5: Silence Handling"
echo "  - Say 'Hey Jarvis' but don't say anything after"
echo "  - Expected: After 2s silence, returns to LISTENING"
echo "  Press Enter when ready..."
read

echo ""
echo "=== Manual Testing Complete ==="
```

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] State transitions match spec
- [ ] Barge-in interrupt works correctly
- [ ] Error handling doesn't crash loop
- [ ] Manual test checklist completed

---

## 🧪 Validation Commands

```bash
# 1. Run unit tests
pytest test_voice_loop.py -v

# 2. Run voice loop in debug mode
python voice_loop.py --debug

# 3. Manual test script
./manual_voice_test.sh

# 4. Stress test (10 consecutive interactions)
for i in {1..10}; do
    echo "Interaction $i"
    python -c "from voice_loop import VoiceLoop; l = VoiceLoop(); l._transition_to(VoiceState.ATTENDING)"
done
```

---

## ✅ Definition of Done

- [ ] Barge-in cleanly interrupts TTS
- [ ] Voice loop cycles through all states correctly
- [ ] Recording captures full conversations
- [ ] Unit tests >90% coverage
- [ ] Manual test checklist complete
- [ ] Loop runs stably for 30+ minutes
- [ ] Recovery from errors without restart

---

## 📁 Files to Create/Modify

| File | Purpose |
|------|---------|
| `Smart_Home/jarvis/barge_in.py` | Barge-in detection |
| `Smart_Home/jarvis/tts_controller.py` | Interruptible TTS |
| `Smart_Home/jarvis/voice_loop.py` | Main voice loop |
| `Smart_Home/jarvis/test_voice_loop.py` | Unit tests |
| `Smart_Home/scripts/manual_voice_test.sh` | Manual test guide |
| `Smart_Home/assets/chime.wav` | Activation sound |

---

## 🔗 Dependencies

**Required from Issue #2:**
- `wake_word_detector.py` — Wake word detection
- `stt_client.py` — Speech-to-text
- `tts_client.py` — Text-to-speech (base)

**Required from Issue #1:**
- `tool_broker/main.py` — process_query function

**Additional:**
```
pytest>=7.0.0
pytest-mock>=3.10.0
```

---

**END OF HANDOFF**
