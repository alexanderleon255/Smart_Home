#!/usr/bin/env python3
"""Unit tests for voice loop functionality."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from jarvis.voice_loop import VoiceLoop, VoiceState
from jarvis.barge_in import BargeInDetector
from jarvis.tts_controller import InterruptibleTTS


class TestStateTransitions:
    """Test state machine transitions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('jarvis.voice_loop.WakeWordDetector'), \
             patch('jarvis.voice_loop.WhisperSTT'), \
             patch('jarvis.voice_loop.InterruptibleTTS'), \
             patch('jarvis.voice_loop.BargeInDetector'):
            self.loop = VoiceLoop()
        
    def test_initial_state_is_listening(self):
        """Test that initial state is LISTENING."""
        assert self.loop.state == VoiceState.LISTENING
        
    def test_wake_word_transitions_to_attending(self):
        """Test wake word detection triggers ATTENDING state."""
        self.loop.wake_word = Mock()
        self.loop.wake_word.wait_for_activation.return_value = True
        
        self.loop._handle_listening()
        
        assert self.loop.state == VoiceState.ATTENDING
        
    def test_speech_transitions_to_processing(self):
        """Test speech input transitions to PROCESSING."""
        self.loop.stt = Mock()
        self.loop.stt.transcript = "Turn on the light"
        self.loop.stt.has_new_text.return_value = False
        
        with patch('time.sleep'):  # Skip actual waiting
            self.loop._handle_attending()
        
        assert self.loop.state == VoiceState.PROCESSING
        assert self.loop.user_input == "Turn on the light"
        
    def test_empty_speech_returns_to_listening(self):
        """Test empty speech returns to LISTENING state."""
        self.loop.stt = Mock()
        self.loop.stt.transcript = ""
        self.loop.stt.has_new_text.return_value = False
        
        with patch('time.sleep'):
            self.loop._handle_attending()
        
        assert self.loop.state == VoiceState.LISTENING
        
    def test_processing_transitions_to_speaking(self):
        """Test processing transitions to SPEAKING state."""
        self.loop.user_input = "Test query"
        
        with patch('jarvis.voice_loop.process_query') as mock_process:
            mock_process.return_value = {"response": "Done!"}
            self.loop._handle_processing()
        
        assert self.loop.state == VoiceState.SPEAKING
        assert self.loop.response == "Done!"


class TestBargeIn:
    """Test barge-in interrupt functionality."""
    
    def test_barge_in_interrupts_speech(self):
        """Test barge-in successfully interrupts TTS."""
        with patch('jarvis.voice_loop.WakeWordDetector'), \
             patch('jarvis.voice_loop.WhisperSTT'), \
             patch('jarvis.voice_loop.InterruptibleTTS'), \
             patch('jarvis.voice_loop.BargeInDetector'):
            loop = VoiceLoop()
        
        loop.tts = Mock()
        loop.tts.speak.return_value = True  # Completed
        loop.barge_in = Mock()
        loop.barge_in.stop_monitoring.return_value = True  # Was interrupted
        
        loop.state = VoiceState.SPEAKING
        loop.response = "This is a test"
        loop._handle_speaking()
        
        assert loop.state == VoiceState.ATTENDING
        
    def test_completed_speech_returns_to_listening(self):
        """Test completed speech without interruption returns to LISTENING."""
        with patch('jarvis.voice_loop.WakeWordDetector'), \
             patch('jarvis.voice_loop.WhisperSTT'), \
             patch('jarvis.voice_loop.InterruptibleTTS'), \
             patch('jarvis.voice_loop.BargeInDetector'):
            loop = VoiceLoop()
        
        loop.tts = Mock()
        loop.tts.speak.return_value = True  # Completed
        loop.barge_in = Mock()
        loop.barge_in.stop_monitoring.return_value = False  # Not interrupted
        
        loop.state = VoiceState.SPEAKING
        loop.response = "Test"
        loop._handle_speaking()
        
        assert loop.state == VoiceState.LISTENING
        
    def test_barge_in_detector_threading(self):
        """Test barge-in detector thread lifecycle."""
        mock_wake = Mock()
        mock_wake.check_once.return_value = False
        mock_tts = Mock()
        
        detector = BargeInDetector(mock_wake, mock_tts)
        
        detector.start_monitoring()
        assert detector._monitoring is True
        assert detector._thread is not None
        
        time.sleep(0.2)  # Let thread run
        
        was_interrupted = detector.stop_monitoring()
        assert was_interrupted is False
        assert detector._monitoring is False


class TestToolBrokerIntegration:
    """Test integration with Tool Broker."""
    
    @patch('jarvis.voice_loop.process_query')
    def test_processing_calls_tool_broker(self, mock_process):
        """Test processing calls tool broker with correct query."""
        mock_process.return_value = {"response": "Done!"}
        
        with patch('jarvis.voice_loop.WakeWordDetector'), \
             patch('jarvis.voice_loop.WhisperSTT'), \
             patch('jarvis.voice_loop.InterruptibleTTS'), \
             patch('jarvis.voice_loop.BargeInDetector'):
            loop = VoiceLoop()
        
        loop.user_input = "Turn on the kitchen light"
        loop._handle_processing()
        
        mock_process.assert_called_once_with("Turn on the kitchen light")
        assert loop.response == "Done!"
        assert loop.state == VoiceState.SPEAKING
        
    @patch('jarvis.voice_loop.process_query')
    def test_processing_handles_error(self, mock_process):
        """Test processing handles errors gracefully."""
        mock_process.side_effect = Exception("API Error")
        
        with patch('jarvis.voice_loop.WakeWordDetector'), \
             patch('jarvis.voice_loop.WhisperSTT'), \
             patch('jarvis.voice_loop.InterruptibleTTS'), \
             patch('jarvis.voice_loop.BargeInDetector'):
            loop = VoiceLoop()
        
        loop.user_input = "Test"
        loop._handle_processing()
        
        assert "apologize" in loop.response.lower()
        assert loop.state == VoiceState.SPEAKING


class TestInterruptibleTTS:
    """Test TTS interruption."""
    
    def test_tts_initialization(self):
        """Test TTS initializes correctly."""
        tts = InterruptibleTTS(voice="test-voice")
        assert tts.voice == "test-voice"
        assert tts._process is None
        
    def test_tts_interrupt_during_speech(self):
        """Test TTS can be interrupted."""
        tts = InterruptibleTTS()
        
        # Mock the process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.wait.return_value = -15  # SIGTERM
        tts._process = mock_process
        
        with patch('os.killpg'), patch('os.getpgid'):
            tts.interrupt()
        
        assert tts._process is None


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
        
        with patch('time.sleep'):
            loop._handle_attending()
        
        # Process
        with patch('jarvis.voice_loop.process_query') as mock_process:
            mock_process.return_value = {"response": "It's 3 PM"}
            loop._handle_processing()
        
        # Speak
        loop.tts = Mock()
        loop.tts.speak.return_value = True
        loop.barge_in = Mock()
        loop.barge_in.stop_monitoring.return_value = False
        loop._handle_speaking()
        
        assert loop.state == VoiceState.LISTENING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
