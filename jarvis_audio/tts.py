"""Text-to-speech using Piper."""

import subprocess
import os
from pathlib import Path
from typing import Optional

# Resolve platform-aware defaults
_HOME = Path.home()
_DEFAULT_PIPER_BIN = os.environ.get(
    "PIPER_PATH",
    str(_HOME / ".local" / "piper" / "piper" / "piper"),
)
_DEFAULT_PIPER_MODEL_DIR = os.environ.get(
    "PIPER_MODEL_DIR",
    str(_HOME / ".local" / "piper" / "models"),
)


class PiperTTS:
    """Text-to-speech synthesis using Piper."""
    
    def __init__(
        self,
        voice_model: str = "en_US-lessac-medium",
        piper_path: str = _DEFAULT_PIPER_BIN,
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
        self._model_dir = Path(_DEFAULT_PIPER_MODEL_DIR)
        
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
        # Resolve model path: if voice_model is not itself a path, look in model dir
        model_arg = self.voice_model
        if not Path(model_arg).exists():
            candidate = self._model_dir / f"{self.voice_model}.onnx"
            if candidate.exists():
                model_arg = str(candidate)

        cmd = [
            str(self.piper_path),
            "--model", model_arg,
            "--output_file", output_file or "-",
        ]
        
        result = subprocess.run(
            cmd,
            input=text.encode(),
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
        # Resolve model path
        model_arg = self.voice_model
        if not Path(model_arg).exists():
            candidate = self._model_dir / f"{self.voice_model}.onnx"
            if candidate.exists():
                model_arg = str(candidate)

        ffplay_env = dict(os.environ)
        if audio_output and audio_output != "default":
            ffplay_env["PULSE_SINK"] = audio_output

        piper_proc = subprocess.Popen(
            [
                str(self.piper_path),
                "--model", model_arg,
                "--output_raw",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        ffplay_proc = subprocess.Popen(
            [
                "ffplay",
                "-f", "s16le",
                "-ar", str(self.sample_rate),
                "-ch_layout", "mono",
                "-nodisp",
                "-autoexit",
                "-",
            ],
            stdin=piper_proc.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=ffplay_env,
        )

        if piper_proc.stdout:
            piper_proc.stdout.close()

        _, stderr = piper_proc.communicate(input=text.encode())
        ffplay_return = ffplay_proc.wait()

        if piper_proc.returncode != 0:
            raise RuntimeError(f"Piper failed: {stderr.decode() if stderr else 'unknown error'}")
        if ffplay_return != 0:
            raise RuntimeError(f"ffplay failed with exit code {ffplay_return}")


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
