# Maximum Push Autonomous Secretary Spec v1.0

**Project:** Smart Home Hub -- Llama Sidecar Autonomous Secretary\
**Revision:** 1.0\
**Generated:** 2026-03-02 10:42 UTC

------------------------------------------------------------------------

# 1. System Purpose

Design a fully autonomous, free & open-source, bidirectional voice
conversation capture and cognitive processing system where:

-   AirPods remain paired to iPhone
-   GPT Desktop runs on Mac
-   Mac performs live transcription, live summarization, structured note
    extraction, memory indexing, and full archival recording
-   All components are free and open-source (FOSS)

------------------------------------------------------------------------

# 2. Core Design Principles

1.  Phone behaves like a phone (portable, AirPods-native)
2.  Mac behaves like a local AI server
3.  All audio is recorded for verification
4.  Live notes update during conversation
5.  Post-session high-accuracy transcript generated
6.  Persistent searchable memory created
7.  Zero paid/proprietary routing tools

------------------------------------------------------------------------

# 3. High-Level Architecture

AirPods\
→ iPhone\
→ SonoBus (FOSS bidirectional audio bridge)\
→ Tailscale tunnel\
→ Mac Hub\
├── GPT Desktop App\
├── BlackHole (virtual audio device)\
├── ffmpeg (recording engine)\
├── whisper.cpp (live + final STT)\
└── Llama sidecar (live secretary + memory engine)

------------------------------------------------------------------------

# 4. Audio Signal Flow

## User Voice Path

AirPods → iPhone → SonoBus → Mac → GPT mic input

## GPT Voice Path

GPT output → BlackHole → SonoBus → iPhone → AirPods

## Recording Path

BlackHole mixed stream → ffmpeg → session_YYYYMMDD.wav

This file is the legal/source-of-truth artifact.

------------------------------------------------------------------------

# 5. Live Processing Pipeline

## 5.1 Live Transcription

-   whisper.cpp streaming mode
-   Chunk interval: 1--3 seconds
-   Output: transcript_live.txt

## 5.2 Live Secretary Engine (Llama)

Every 20--30 seconds: - Parse rolling transcript - Update notes_live.md

Live structured sections: - Rolling Summary - Decisions - Action Items
(owner + date if detected) - Open Questions - Memory Candidates -
Automation Opportunities

------------------------------------------------------------------------

# 6. Post-Session Finalization

1.  Re-run whisper.cpp high-accuracy pass
2.  Optional speaker diarization
3.  Generate:
    -   transcript_final.txt
    -   notes_final.md
    -   memory_update.json
4.  Archive all artifacts under:

/hub_sessions/YYYY/MM/DD/session_id/

Artifacts: - raw_audio.wav - transcript_live.txt -
transcript_final.txt - notes_live.md - notes_final.md -
memory_update.json

------------------------------------------------------------------------

# 7. Memory Architecture

## 7.1 Structured Memory Layers

### Ephemeral

Session-only rolling buffer

### Persistent Structured

-   Preferences
-   Decisions
-   Long-term goals
-   Project references

### Vector Memory

-   Embeddings of transcript chunks
-   Semantic search enabled

------------------------------------------------------------------------

# 8. Automation Hooks

Trigger phrases such as: - "Remind me" - "We should automate" - "Next
week" - "Add that to the list"

Auto-generate: - Reminder objects - Smart home task suggestions - Review
queue items

------------------------------------------------------------------------

# 9. Security Model

-   All processing local to Mac
-   No cloud transcription
-   Audio files encrypted at rest (optional future rev)
-   Tailscale zero-trust network access
-   No proprietary routing tools

------------------------------------------------------------------------

# 10. Performance Expectations (M1 Mac)

-   Real-time whisper.cpp small/medium model
-   Llama 7B--13B summarization
-   Sub-5 second rolling update latency
-   Stable full-duplex audio

------------------------------------------------------------------------

# 11. Future Expansion (Maximum Push Mode)

-   Daily auto-digest generation
-   Weekly operational review
-   Behavioral pattern detection
-   Smart home anomaly correlation
-   Emotional tone tracking
-   Cross-session decision drift detection
-   Searchable life-log UI

------------------------------------------------------------------------

# 12. Success Criteria

System is considered fully operational when:

-   User conducts GPT voice conversation via AirPods
-   Live notes update visibly during session
-   Full transcript and audio recording saved
-   Structured summary generated automatically
-   Memory indexed and searchable
-   Zero paid software dependencies

------------------------------------------------------------------------

END OF SPEC v1.0
