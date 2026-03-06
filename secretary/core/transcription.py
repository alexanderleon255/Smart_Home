"""Transcription engine for live audio capture."""

import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from ..config import secretary_config
from ..schemas import TranscriptionChunk

logger = logging.getLogger(__name__)


class TranscriptionEngine:
    """
    Manages live transcription using whisper.cpp.
    
    Provides streaming transcription with rolling buffer and timestamp markers.
    Implements P7-01: Live Transcription Pipeline.
    """
    
    def __init__(
        self,
        model: str = None,
        chunk_seconds: int = None,
        session_dir: Path = None,
    ):
        """
        Initialize transcription engine.
        
        Args:
            model: Whisper model to use (tiny/base/small/medium/large)
            chunk_seconds: Seconds between transcription chunks
            session_dir: Directory to write transcript files
        """
        self.model = model or secretary_config.whisper_model
        self.chunk_seconds = chunk_seconds or secretary_config.transcription_chunk_seconds
        self.session_dir = session_dir or Path.cwd()
        
        self.transcript_file = self.session_dir / secretary_config.transcript_live_file
        self.transcript_buffer = []
        self.is_running = False
    
    async def start_streaming(self, audio_source: str) -> AsyncGenerator[TranscriptionChunk, None]:
        """
        Start streaming transcription from audio source using whisper.cpp.
        
        Args:
            audio_source: Path to audio file or stream URL
            
        Yields:
            TranscriptionChunk objects with timestamp and text
        """
        import os
        from pathlib import Path
        
        self.is_running = True
        self.transcript_file.write_text("")  # Clear file
        
        logger.info(f"Starting transcription stream from {audio_source}")
        
        try:
            # Build whisper.cpp command
            whisper_bin = Path(secretary_config.whisper_model_path).parent / "whisper-cli"
            if not whisper_bin.exists():
                # Fallback to system PATH
                whisper_bin = "whisper-cli"
            
            cmd = [
                str(whisper_bin),
                "-m", secretary_config.whisper_model,
                "-l", "en",
                "-otxt",
                str(audio_source)
            ]
            
            # Run whisper.cpp process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"whisper.cpp failed: {error_msg}")
                raise RuntimeError(f"Transcription failed: {error_msg}")
            
            # Parse output (whisper.cpp writes to .txt file)
            output_file = Path(str(audio_source) + ".txt")
            if output_file.exists():
                text = output_file.read_text().strip()
                output_file.unlink()  # Clean up temp file
            else:
                # Try parsing stdout
                text = stdout.decode().strip()
            
            if text:
                chunk = TranscriptionChunk(
                    timestamp=datetime.utcnow(),
                    text=text,
                    confidence=0.95  # whisper.cpp doesn't provide per-word confidence
                )
                self._write_chunk(chunk)
                yield chunk
            else:
                logger.warning(f"whisper.cpp produced no output for {audio_source}")
                
        except Exception as e:
            logger.error(f"Transcription stream error: {e}")
            raise
        finally:
            self.is_running = False
    
    def _write_chunk(self, chunk: TranscriptionChunk):
        """Write chunk to transcript file with timestamp."""
        timestamp_str = chunk.timestamp.strftime("%H:%M:%S")
        line = f"[{timestamp_str}] {chunk.text}\n"
        
        # Append to file
        with self.transcript_file.open("a") as f:
            f.write(line)
        
        # Add to buffer
        self.transcript_buffer.append(chunk)
    
    def get_rolling_buffer(self, window_seconds: int = 300) -> str:
        """
        Get recent transcript window.
        
        Args:
            window_seconds: Size of rolling window in seconds
            
        Returns:
            Concatenated transcript text from window
        """
        cutoff_time = datetime.utcnow().timestamp() - window_seconds
        
        recent_chunks = [
            chunk for chunk in self.transcript_buffer
            if chunk.timestamp.timestamp() >= cutoff_time
        ]
        
        return "\n".join(chunk.text for chunk in recent_chunks)
    
    def stop(self):
        """Stop the transcription stream."""
        logger.info("Stopping transcription stream")
        self.is_running = False
    
    async def process_audio_file(self, audio_file: Path, high_accuracy: bool = False) -> str:
        """
        Process complete audio file for high-accuracy transcription.
        
        Used for P7-03: High-Accuracy Post-Processing.
        
        Args:
            audio_file: Path to audio file
            high_accuracy: Use high-accuracy model
            
        Returns:
            Full transcript text
        """
        model = secretary_config.high_accuracy_model if high_accuracy else self.model
        
        logger.info(f"Processing audio file {audio_file} with model {model}")
        
        # Placeholder: would run whisper.cpp in batch mode
        # Example command:
        # whisper.cpp --model {model} --output-txt {audio_file}
        
        # For now, return placeholder
        output_file = self.session_dir / secretary_config.transcript_final_file
        
        try:
            # Real implementation would call whisper.cpp here
            # subprocess.run([
            #     "whisper.cpp",
            #     "--model", model,
            #     "--output-txt",
            #     str(audio_file)
            # ], check=True)
            
            # Placeholder
            transcript = f"[High-accuracy transcript of {audio_file.name}]\n"
            output_file.write_text(transcript)
            
            logger.info(f"Wrote final transcript to {output_file}")
            return transcript
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Whisper processing failed: {e}")
            raise
