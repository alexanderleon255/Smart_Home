"""Speech-to-text using whisper.cpp."""

import subprocess
import os
from pathlib import Path
from typing import Optional, Generator


class WhisperSTT:
    """Speech-to-text transcription using whisper.cpp."""
    
    def __init__(
        self,
        model_path: str = "models/ggml-small.bin",
        whisper_cpp_path: str = "whisper.cpp/main",
        streaming: bool = True,
    ):
        """Initialize Whisper STT.
        
        Args:
            model_path: Path to Whisper GGML model file
            whisper_cpp_path: Path to whisper.cpp executable
            streaming: Enable streaming mode
        """
        self.model_path = Path(model_path)
        self.whisper_cpp_path = Path(whisper_cpp_path)
        self.streaming = streaming
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        if not self.whisper_cpp_path.exists():
            raise FileNotFoundError(f"whisper.cpp not found: {whisper_cpp_path}")
    
    def transcribe_file(self, audio_file: str) -> str:
        """Transcribe an audio file.
        
        Args:
            audio_file: Path to audio file (WAV format)
            
        Returns:
            Transcribed text
        """
        cmd = [
            str(self.whisper_cpp_path),
            "-m", str(self.model_path),
            "-f", audio_file,
            "--no-timestamps",
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"whisper.cpp failed: {result.stderr}")
        
        # Extract text from output (whisper.cpp prints to stdout)
        text = result.stdout.strip()
        return text
    
    def transcribe_stream(self, audio_device: str = "default") -> Generator[str, None, None]:
        """Transcribe audio stream in real-time.
        
        Args:
            audio_device: Audio input device
            
        Yields:
            Transcribed text chunks
        """
        if not self.streaming:
            raise ValueError("Streaming mode not enabled")
        
        cmd = [
            str(self.whisper_cpp_path),
            "-m", str(self.model_path),
            "--stream",
            "--audio-ctx", "768",  # 1-3 second chunks
            "--no-timestamps",
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    yield line.strip()
        finally:
            process.terminate()


def main():
    """Test speech-to-text."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python stt.py <audio_file.wav>")
        print("   or: python stt.py --stream")
        sys.exit(1)
    
    stt = WhisperSTT()
    
    if sys.argv[1] == "--stream":
        print("Starting streaming transcription...")
        print("Speak into your microphone. Press Ctrl+C to stop.")
        try:
            for text in stt.transcribe_stream():
                print(f">>> {text}")
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        audio_file = sys.argv[1]
        print(f"Transcribing: {audio_file}")
        text = stt.transcribe_file(audio_file)
        print(f"\nTranscript:\n{text}")


if __name__ == "__main__":
    main()
