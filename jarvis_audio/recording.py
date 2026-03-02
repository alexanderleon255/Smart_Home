"""Audio recording using ffmpeg."""

import subprocess
import signal
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class AudioRecorder:
    """Records audio using ffmpeg with BlackHole virtual device."""
    
    def __init__(
        self,
        output_dir: str = "./sessions",
        sample_rate: int = 16000,
        audio_device: str = "BlackHole 2ch",
    ):
        """Initialize audio recorder.
        
        Args:
            output_dir: Directory to save recordings
            sample_rate: Recording sample rate (Hz)
            audio_device: Audio input device name
        """
        self.output_dir = Path(output_dir)
        self.sample_rate = sample_rate
        self.audio_device = audio_device
        self.process: Optional[subprocess.Popen] = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def start_recording(self, output_file: Optional[str] = None) -> str:
        """Start recording audio.
        
        Args:
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Path to output file
        """
        if self.process is not None:
            raise RuntimeError("Recording already in progress")
        
        # Auto-generate filename
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"session_{timestamp}.wav"
        else:
            output_file = Path(output_file)
        
        # ffmpeg command for macOS with BlackHole
        cmd = [
            "ffmpeg",
            "-f", "avfoundation",
            "-i", f":{self.audio_device}",  # Audio only from BlackHole
            "-ar", str(self.sample_rate),
            "-ac", "2",  # Stereo
            "-y",  # Overwrite output file
            str(output_file),
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        
        print(f"Recording started: {output_file}")
        return str(output_file)
    
    def stop_recording(self):
        """Stop recording audio."""
        if self.process is None:
            raise RuntimeError("No recording in progress")
        
        # Send interrupt signal to ffmpeg
        self.process.send_signal(signal.SIGINT)
        
        # Wait for process to finish
        self.process.wait(timeout=5)
        
        print("Recording stopped")
        self.process = None
    
    def is_recording(self) -> bool:
        """Check if currently recording.
        
        Returns:
            True if recording in progress
        """
        return self.process is not None and self.process.poll() is None


def main():
    """Test audio recording."""
    import sys
    import time
    
    if len(sys.argv) < 2:
        print("Usage: python recording.py <duration_seconds>")
        print("   or: python recording.py --output <file.wav> <duration_seconds>")
        sys.exit(1)
    
    recorder = AudioRecorder()
    
    if sys.argv[1] == "--output":
        if len(sys.argv) < 4:
            print("Usage: python recording.py --output <file.wav> <duration_seconds>")
            sys.exit(1)
        output_file = sys.argv[2]
        duration = int(sys.argv[3])
    else:
        output_file = None
        duration = int(sys.argv[1])
    
    print(f"Recording for {duration} seconds...")
    output_path = recorder.start_recording(output_file)
    
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        print("\nInterrupted!")
    finally:
        recorder.stop_recording()
        print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
