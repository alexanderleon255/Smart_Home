"""
Example usage of the Secretary Pipeline.

This demonstrates the full workflow from session creation through archival.
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime

from secretary import TranscriptionEngine, SecretaryEngine, ArchivalSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_example_session():
    """Run a complete secretary session example."""
    
    # Initialize components
    archival = ArchivalSystem()
    session_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    session_dir = archival.create_session_directory(session_id)
    
    logger.info(f"Starting secretary session: {session_id}")
    logger.info(f"Session directory: {session_dir}")
    
    # Initialize transcription and secretary engines
    transcription = TranscriptionEngine(session_dir=session_dir)
    secretary = SecretaryEngine(session_dir=session_dir)
    
    # Simulate a conversation (in real usage, this would be live audio)
    example_transcript = """
    [10:15:23] Hey, I wanted to discuss the smart home automation project.
    [10:15:30] We should prioritize the secretary pipeline implementation first.
    [10:15:45] I think using Llama 3.1 for the note extraction makes sense.
    [10:16:00] Can you remind me to review the progress next Tuesday?
    [10:16:15] We also need to decide on the whisper model - probably base or small.
    [10:16:30] Let's use the base model for live transcription and small for final pass.
    [10:16:45] Action item for me: write unit tests by end of week.
    [10:17:00] And we should automate the daily session cleanup.
    [10:17:15] One question - do we need speaker diarization for multi-person calls?
    [10:17:30] I prefer concise summaries, not verbose ones.
    """
    
    # Write example transcript
    transcript_file = session_dir / "transcript_live.txt"
    transcript_file.write_text(example_transcript)
    
    logger.info("Processing transcript with secretary engine...")
    
    # Process with secretary engine
    await secretary._update_live_notes(example_transcript)
    
    logger.info("Generated live notes:")
    print("\n" + "="*60)
    print(secretary.current_notes.to_markdown())
    print("="*60 + "\n")
    
    # Generate final notes
    logger.info("Generating final comprehensive notes...")
    final_notes = await secretary.generate_final_notes(example_transcript)
    print("\nFinal Notes:")
    print("="*60)
    print(final_notes)
    print("="*60 + "\n")
    
    # Generate memory update
    logger.info("Extracting memory updates...")
    memory_update = await secretary.generate_memory_update(example_transcript, session_id)
    print(f"\nMemory Update: {len(memory_update.extractions)} extractions")
    
    # Detect automation hooks
    logger.info("Detecting automation hooks...")
    automation = await secretary.detect_automation_hooks(example_transcript)
    print(f"\nAutomation Opportunities: {len(automation.get('opportunities', []))}")
    
    # Archive the session
    logger.info("Archiving session...")
    metadata = {
        "duration_minutes": 2,
        "participants": ["user"],
        "topics": ["smart home", "secretary pipeline"],
    }
    archival.archive_session(session_dir, session_id, metadata)
    
    # Show archival stats
    stats = archival.get_session_stats()
    print("\nArchival Stats:")
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  Total size: {stats['total_size_mb']} MB")
    
    logger.info(f"Session {session_id} complete!")
    
    return session_dir


async def main():
    """Main entry point."""
    print("="*60)
    print("Secretary Pipeline - Example Session")
    print("="*60 + "\n")
    
    try:
        session_dir = await run_example_session()
        print(f"\n✅ Session completed successfully!")
        print(f"📁 Session files: {session_dir}")
        
    except Exception as e:
        logger.error(f"Session failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
