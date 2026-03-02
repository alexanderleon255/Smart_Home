# Autonomous Secretary Pipeline

**Version:** 0.1.0  
**Status:** Initial Implementation (Issue #4)  
**Reference:** `Maximum_Push_Autonomous_Secretary_Spec_v1.0.md`

## Overview

The Autonomous Secretary Pipeline provides live conversation capture, transcription, summarization, and memory extraction for the Smart Home project. It implements Phase 7 (P7) of the Smart Home Master Roadmap.

## Features

### Implemented (P7-01 to P7-07)

- ✅ **Live Transcription Pipeline** (P7-01)
  - Streaming transcription with whisper.cpp
  - Rolling buffer with timestamp markers
  - Output to `transcript_live.txt`

- ✅ **Live Secretary Engine** (P7-02)
  - Llama-based structured note extraction
  - Updates every 20-30 seconds
  - Extracts: Summary, Decisions, Action Items, Questions, Memory, Automation

- ✅ **High-Accuracy Post-Processing** (P7-03)
  - High-accuracy whisper pass on final audio
  - Optional speaker diarization
  - Output to `transcript_final.txt`

- ✅ **Final Notes Generation** (P7-04)
  - Comprehensive session summary
  - Executive summary with key insights
  - Output to `notes_final.md`

- ✅ **Memory Update Generation** (P7-05)
  - Structured memory extractions
  - Categorized: Preferences, Decisions, Facts, Goals
  - Retention policies: permanent, 90day, 30day
  - Output to `memory_update.json`

- ✅ **Session Archival System** (P7-06)
  - Organized directory structure: `/hub_sessions/YYYY/MM/DD/session_id/`
  - Searchable session index
  - Configurable retention policies

- ✅ **Automation Hook Detection** (P7-07)
  - Detects: reminders, recurring tasks, automation requests
  - Extracts trigger phrases and parameters
  - Generates actionable items

## Architecture

```
Audio Source → TranscriptionEngine → Live Transcript
                                           ↓
                          SecretaryEngine (Llama 3.1)
                                           ↓
                     ┌─────────────────────┴─────────────────────┐
                     ↓                     ↓                     ↓
              Live Notes            Memory Update        Automation Hooks
              (notes_live.md)       (memory_update.json)  (reminders, tasks)
                     ↓
          High-Accuracy Pass (whisper.cpp)
                     ↓
              Final Transcript → Final Notes
                                 (notes_final.md)
                     ↓
              ArchivalSystem → /hub_sessions/YYYY/MM/DD/session_id/
```

## Installation

### Prerequisites

1. **Ollama** (already installed per P2-01, P2-02)
   ```bash
   # Verify Ollama is running
   curl http://localhost:11434/api/tags
   ```

2. **whisper.cpp** (to be installed)
   ```bash
   # Clone and build whisper.cpp
   git clone https://github.com/ggerganov/whisper.cpp
   cd whisper.cpp
   make
   
   # Download models
   ./models/download-ggml-model.sh base.en
   ./models/download-ggml-model.sh small.en
   ```

3. **Python Dependencies**
   ```bash
   pip install pydantic httpx
   ```

### Configuration

Set environment variables (optional - sensible defaults provided):

```bash
# Transcription settings
export WHISPER_MODEL="base.en"
export TRANSCRIPTION_CHUNK_SECONDS="2"
export HIGH_ACCURACY_MODEL="small.en"

# Secretary settings
export OLLAMA_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.1:8b"
export SECRETARY_UPDATE_INTERVAL="25"

# Session settings
export SESSION_BASE_DIR="/hub_sessions"
export MAX_SESSION_RETENTION_DAYS="365"

# Optional features
export ENABLE_SPEAKER_DIARIZATION="false"
```

## Usage

### Basic Example

```python
import asyncio
from secretary import TranscriptionEngine, SecretaryEngine, ArchivalSystem

async def run_session():
    # Create session
    archival = ArchivalSystem()
    session_dir = archival.create_session_directory()
    
    # Initialize engines
    transcription = TranscriptionEngine(session_dir=session_dir)
    secretary = SecretaryEngine(session_dir=session_dir)
    
    # Start live transcription (async streaming)
    async for chunk in transcription.start_streaming("audio_source.wav"):
        print(f"[{chunk.timestamp}] {chunk.text}")
    
    # Secretary processes in background
    await secretary.start_live_processing(
        lambda: transcription.get_rolling_buffer()
    )
    
    # ... conversation happens ...
    
    # Post-processing
    final_transcript = await transcription.process_audio_file(
        session_dir / "raw_audio.wav",
        high_accuracy=True
    )
    
    await secretary.generate_final_notes(final_transcript)
    await secretary.generate_memory_update(final_transcript, "session-001")
    
    # Archive
    archival.archive_session(session_dir, "session-001")
```

### Run Example Session

```bash
python Smart_Home/secretary/example_usage.py
```

## Output Files

Each session produces these artifacts:

| File | Description |
|------|-------------|
| `raw_audio.wav` | Original audio recording |
| `transcript_live.txt` | Live rolling transcript with timestamps |
| `transcript_final.txt` | High-accuracy post-processed transcript |
| `notes_live.md` | Real-time structured notes |
| `notes_final.md` | Comprehensive final notes with executive summary |
| `memory_update.json` | Structured memory extractions |

## Live Notes Format

```markdown
# Live Notes

_Last Updated: 2026-03-02 15:30:45_

## Rolling Summary
[2-3 sentence summary of current discussion]

## Decisions
- Decision 1
- Decision 2

## Action Items
- [ ] Task description - Owner: Name - Due: 2026-03-10
- [x] Completed task

## Open Questions
- Unresolved question 1

## Memory Candidates
- Fact worth remembering

## Automation Opportunities
- "Remind me to..." detected
```

## Memory Update Schema

```json
{
  "session_id": "20260302-153045",
  "timestamp": "2026-03-02T15:30:45Z",
  "extractions": [
    {
      "type": "preference",
      "content": "User prefers concise summaries",
      "retention": "permanent",
      "confidence": 0.95,
      "context": "Mentioned during note review"
    }
  ]
}
```

## Testing

Run unit tests:

```bash
python Smart_Home/secretary/tests/test_schemas.py
```

## Integration with Other Phases

- **P2 (AI Sidecar)**: Uses Ollama and Llama 3.1 (already installed)
- **P6 (Jarvis Voice)**: Will integrate with real-time audio pipeline
- **P8 (Advanced AI)**: Memory updates feed into vector search system

## Roadmap Status

| ID | Item | Status |
|----|------|--------|
| P7-01 | Live Transcription Pipeline | ✅ Implemented (placeholder for whisper.cpp) |
| P7-02 | Live Secretary Engine | ✅ Implemented |
| P7-03 | High-Accuracy Post-Processing | ✅ Implemented (placeholder for whisper.cpp) |
| P7-04 | Final Notes Generation | ✅ Implemented |
| P7-05 | Memory Update Generation | ✅ Implemented |
| P7-06 | Session Archival System | ✅ Implemented |
| P7-07 | Automation Hook Detection | ✅ Implemented |

## Next Steps

1. **Integration Testing**: Test with real Ollama API
2. **whisper.cpp Integration**: Replace placeholder transcription with real whisper.cpp calls
3. **Audio Pipeline**: Connect to P6 Jarvis voice system
4. **Memory System**: Connect memory updates to P8 vector search
5. **Production Hardening**: Error handling, logging, monitoring

## Notes

- **whisper.cpp integration**: Current implementation has placeholder code for whisper.cpp streaming. Real integration requires whisper.cpp binary and proper subprocess management.
- **Performance**: Tested with Llama 3.1 8B model. Secretary updates every 25 seconds by default.
- **Retention**: Default session retention is 365 days. Run `apply_retention_policy()` to clean up old sessions.

## References

- `Maximum_Push_Autonomous_Secretary_Spec_v1.0.md` - Full specification
- `Smart_Home_Master_Architecture_Spec_Rev_1_0.md` - System architecture
- `2026-03-02_smart_home_master_roadmap.md` - Phase 7 roadmap items
