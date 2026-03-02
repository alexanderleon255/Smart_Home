"""Text-to-speech using Piper."""

import subprocess
import os
from pathlib import Path
from typing import Optional


class PiperTTS:
    """Text-to-speech synthesis using Piper."""
    
    def __init__(
        self,
        voice_model: str = "en_US-lessac-medium",
        piper_path: str = "piper/piper",
        sample_rate: int = 22050,
    ):
        """Initialize Piper TTS.
        
        Args:
            voice_model: Piper voice model name
            piper_path: Path to Piper executable
            sample_rate: Output sample rate (Hz)
        """
        self.voice_model = voice_model
        self.piper_path = Path(piper_path)
        self.sample_rate = sample_rate
        
        if not self.piper_path.exists():
            raise FileNotFoundError(f"Piper not found: {piper_path}")
    
    def synthesize(self, text: str, output_file: Optional[str] = None) -> bytes:
        """Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            output_file: Optional WAV file to save (if None, returns audio bytes)
            
        Returns:
            WAV audio data (if output_file is None)
        """
        cmd = [
            str(self.piper_path),
            "--model", self.voice_model,
            "--output_file", output_file or "-",
        ]
        
        result = subprocess.run(
            cmd,
            input=text,
            capture_output=True,
            text=False,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Piper failed: {result.stderr.decode()}")
        
        if output_file:
            return None
        else:
            return result.stdout
    
    def synthesize_streaming(self, text: str, audio_output: str = "default"):
        """Synthesize speech with streaming output.
        
        Args:
            text: Text to synthesize
            audio_output: Audio output device
        """
        cmd = [
            str(self.piper_path),
            "--model", self.voice_model,
            "--output-raw",
            "|",
            "ffplay", "-nodisp", "-autoexit", "-i", "-",
        ]
        
        process = subprocess.Popen(
            " ".join(cmd),
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        process.communicate(input=text.encode())


def main():
    """Test text-to-speech."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tts.py <text>")
        print("   or: python tts.py --file <text_file> <output.wav>")
        sys.exit(1)
    
    tts = PiperTTS()
    
    if sys.argv[1] == "--file":
        if len(sys.argv) < 4:
            print("Usage: python tts.py --file <text_file> <output.wav>")
            sys.exit(1)
        
        with open(sys.argv[2], 'r') as f:
            text = f.read()
        
        output_file = sys.argv[3]
        print(f"Synthesizing to: {output_file}")
        tts.synthesize(text, output_file)
        print("Done!")
    else:
        text = " ".join(sys.argv[1:])
        print(f"Synthesizing: {text}")
        tts.synthesize_streaming(text)


if __name__ == "__main__":
    main()
