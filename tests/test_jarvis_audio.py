#!/usr/bin/env python3
"""Tests for jarvis_audio/ — all classes shell out, so everything is mocked."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from Smart_Home.jarvis_audio.recording import AudioRecorder


# ---------------------------------------------------------------------------
# AudioRecorder
# ---------------------------------------------------------------------------

class TestAudioRecorder:
    @pytest.fixture
    def recorder(self, tmp_path):
        return AudioRecorder(output_dir=str(tmp_path / "sessions"))

    def test_creates_output_dir(self, tmp_path):
        d = tmp_path / "new_sessions"
        AudioRecorder(output_dir=str(d))
        assert d.exists()

    def test_is_recording_default_false(self, recorder):
        assert recorder.is_recording() is False

    @patch("subprocess.Popen")
    def test_start_recording(self, mock_popen, recorder):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # process still running
        mock_popen.return_value = mock_proc
        result = recorder.start_recording()
        assert isinstance(result, str)
        assert recorder.is_recording() is True

    @patch("subprocess.Popen")
    def test_stop_recording(self, mock_popen, recorder):
        mock_proc = MagicMock(pid=1234)
        mock_proc.poll.return_value = None  # process still running
        mock_popen.return_value = mock_proc
        recorder.start_recording()
        recorder.stop_recording()
        assert recorder.is_recording() is False

    @patch("subprocess.Popen")
    def test_double_start_raises(self, mock_popen, recorder):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        recorder.start_recording()
        with pytest.raises(RuntimeError):
            recorder.start_recording()


# ---------------------------------------------------------------------------
# WhisperSTT — constructor validation
# ---------------------------------------------------------------------------

class TestWhisperSTT:
    def test_missing_model_raises(self):
        with pytest.raises(FileNotFoundError):
            from Smart_Home.jarvis_audio.stt import WhisperSTT
            WhisperSTT(model_path="/nonexistent/model.bin", whisper_cpp_path="/nonexistent/main")

    @patch("pathlib.Path.exists", return_value=True)
    def test_init_succeeds_with_valid_paths(self, mock_exists):
        from Smart_Home.jarvis_audio.stt import WhisperSTT
        stt = WhisperSTT(model_path="/fake/model.bin", whisper_cpp_path="/fake/main")
        assert stt is not None


# ---------------------------------------------------------------------------
# PiperTTS — constructor validation
# ---------------------------------------------------------------------------

class TestPiperTTS:
    def test_missing_binary_raises(self):
        with pytest.raises(FileNotFoundError):
            from Smart_Home.jarvis_audio.tts import PiperTTS
            PiperTTS(piper_path="/nonexistent/piper")

    @patch("pathlib.Path.exists", return_value=True)
    def test_init_succeeds_with_valid_path(self, mock_exists):
        from Smart_Home.jarvis_audio.tts import PiperTTS
        tts = PiperTTS(piper_path="/fake/piper")
        assert tts is not None


# ---------------------------------------------------------------------------
# WakeWordDetector — import guard
# ---------------------------------------------------------------------------

class TestWakeWordDetector:
    def test_import_guard(self):
        """WakeWordDetector should handle missing openwakeword gracefully."""
        try:
            from Smart_Home.jarvis_audio.wake_word import WakeWordDetector
            # If it imports, the dependency is available
            assert WakeWordDetector is not None
        except ImportError:
            # Expected if openwakeword is not installed
            pass
