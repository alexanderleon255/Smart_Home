# [Background Agent] Issue #4: Secretary Pipeline

**Roadmap Items:** P7-01, P7-02, P7-03, P7-04, P7-05, P7-06, P7-07  
**Estimated Effort:** 12-15h total  
**Estimated LOC:** ~400  
**Priority:** MEDIUM (enables ambient intelligence)  
**Dependencies:** None (uses Ollama directly, builds own whisper.cpp)  
**Parallel Track:** WAVE 1 — Can start immediately alongside Issues #1 and #2

---

## 🎯 Objective

Build the "Secretary" ambient intelligence pipeline that passively listens to conversations, creates smart home automations, extracts insights, and maintains a knowledge archive. The Secretary never speaks but enhances the home through observation.

---

## 📚 Context to Load

**Required Reading:**
- `Smart_Home/AI_CONTEXT/SOURCES/vision_document.md` — §5.5 (Secretary Pipeline w/ diagram)
- `Smart_Home/References/Secretary_Ambient_Architecture_v1.0.md` — Full spec
- `Smart_Home/References/Explicit_Interface_Contracts_v1.0.md` — §4 (Memory Layer: structured state, event log, vector memory schemas)

**Pipeline Architecture:**
```
LIVE PROCESSING (streaming) → 30s chunks → transcript + provisional notes

POST-SESSION (batch) → After conversation ends:
  - Clean transcript
  - Extract entities/preferences
  - Identify automation candidates

ARCHIVAL (nightly) → Compress & index:
  - Archive sessions
  - Generate daily digest
  - Update vector memory
```

**Secretary Principles:**
1. **Silent** — Never interrupts, never speaks
2. **Ambient** — Always listening when mic open
3. **Helpful** — Surfaces insights to user through Home Assistant UI
4. **Private** — All processing local, user controls retention

---

## ⚙️ Setup Prerequisites (First Steps)

**This issue is INDEPENDENT — builds own whisper.cpp and Ollama model.**

### 1. Build whisper.cpp (Required)
```bash
cd ~/Developer/BoltPatternSuiteV.1/Smart_Home

# Clone and build whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make

# Download model
./models/download-ggml-model.sh small.en

# Verify
./stream --help
```

### 2. Verify Ollama is Running
```bash
# Check Ollama is available (should already be running from P2-01/P2-02)
curl http://localhost:11434/api/tags
```

### 3. Build Secretary Modelfile
```bash
cd ~/Developer/BoltPatternSuiteV.1/Smart_Home
ollama create secretary -f Modelfile.secretary
```

---

## 📋 Detailed Tasks

### P7-01: Live Transcription Service — 2h

**Goal:** Continuous transcription with 30-second chunked output

**Service Implementation:**
```python
#!/usr/bin/env python3
# secretary/live_transcript.py

import os
import time
import subprocess
from datetime import datetime
from pathlib import Path

class LiveTranscriptService:
    """Continuous transcription for Secretary ambient listening."""
    
    def __init__(
        self, 
        output_dir: str = "~/hub_sessions",
        chunk_duration: int = 30,
        whisper_model: str = "./whisper.cpp/models/ggml-small.en.bin"
    ):
        self.output_dir = Path(output_dir).expanduser()
        self.chunk_duration = chunk_duration
        self.whisper_model = whisper_model
        self._running = False
        self._process = None
        
        # Session state
        self.session_dir = None
        self.transcript_file = None
        
    def start_session(self) -> Path:
        """Start a new transcription session."""
        # Create session directory
        timestamp = datetime.now()
        self.session_dir = self.output_dir / timestamp.strftime("%Y/%m/%d")
        self.session_dir /= f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Transcript output file
        self.transcript_file = self.session_dir / "live_transcript.txt"
        
        # Start whisper.cpp in streaming mode
        self._running = True
        self._start_whisper()
        
        print(f"Secretary session started: {self.session_dir}")
        return self.session_dir
        
    def stop_session(self) -> Path:
        """Stop the current session."""
        self._running = False
        if self._process:
            self._process.terminate()
            self._process.wait()
            self._process = None
        
        print(f"Secretary session ended: {self.session_dir}")
        return self.session_dir
        
    def _start_whisper(self):
        """Start whisper.cpp streaming process."""
        cmd = [
            "./whisper.cpp/stream",
            "-m", self.whisper_model,
            "--print-realtime",
            "--no-timestamps",
            "--threads", "4",
            "--step", "3000",   # 3s step
            "--length", "30000" # 30s window
        ]
        
        # Output to file
        with open(self.transcript_file, 'a') as f:
            self._process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.DEVNULL
            )


class ChunkedTranscriptProcessor:
    """Process transcript file in 30-second chunks."""
    
    def __init__(self, transcript_file: Path):
        self.transcript_file = transcript_file
        self.last_position = 0
        
    def get_new_chunks(self):
        """Yield new 30-second chunks since last read."""
        with open(self.transcript_file, 'r') as f:
            f.seek(self.last_position)
            content = f.read()
            self.last_position = f.tell()
            
        if content.strip():
            # Split into ~30s chunks (rough estimate: 150 words)
            words = content.split()
            chunk_size = 150  # ~30s of speech
            
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i+chunk_size])
                yield chunk


if __name__ == "__main__":
    service = LiveTranscriptService()
    session_dir = service.start_session()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop_session()
```

**Acceptance Criteria:**
- [ ] Continuous transcription from SonoBus/BlackHole
- [ ] Output to session directory structure
- [ ] ~30s chunked processing
- [ ] Graceful start/stop

---

### P7-02: Live Secretary Engine — 3h

**Goal:** Real-time analysis of conversation chunks

**Secretary Modelfile:**
```dockerfile
# Modelfile for Secretary
# Build: ollama create secretary -f Modelfile.secretary

FROM llama3.1:8b-instruct

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 2048
PARAMETER stop "<|eot_id|>"

SYSTEM """
You are Secretary, a silent ambient intelligence assistant.

Your role:
- Analyze conversation transcripts
- Identify actionable items (todos, reminders, preferences)
- Detect automation opportunities
- Extract entities (people, places, times, products)

Output format (JSON only):
{
  "summary": "1-2 sentence summary of chunk",
  "entities": [{"type": "person|place|time|product", "value": "..."}],
  "action_items": ["todo 1", "todo 2"],
  "automation_candidates": [
    {"trigger": "...", "action": "...", "confidence": 0.0-1.0}
  ],
  "preferences_detected": [
    {"category": "...", "preference": "...", "source_quote": "..."}
  ]
}

Rules:
- Output ONLY valid JSON, no commentary
- Confidence < 0.5 = uncertain, don't suggest
- Never fabricate entities not in transcript
- Focus on home automation opportunities
"""
```

**Live Secretary Service:**
```python
#!/usr/bin/env python3
# secretary/live_engine.py

import json
import httpx
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

OLLAMA_URL = "http://localhost:11434"

class LiveSecretaryEngine:
    """Real-time analysis of conversation chunks."""
    
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.notes_file = session_dir / "secretary_notes.jsonl"
        self.entities_file = session_dir / "entities.json"
        
        # Accumulate entities across session
        self.all_entities: List[Dict] = []
        self.all_action_items: List[str] = []
        self.all_automations: List[Dict] = []
        self.all_preferences: List[Dict] = []
        
    def process_chunk(self, chunk_text: str) -> Dict[str, Any]:
        """Process a 30-second transcript chunk."""
        prompt = f"""Analyze this conversation transcript chunk:

---
{chunk_text}
---

Extract entities, action items, automation candidates, and preferences. Output JSON only."""

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "secretary",
                "prompt": prompt,
                "stream": False
            },
            timeout=30.0
        )
        
        result_text = response.json().get("response", "{}")
        
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            result = {"summary": "Parse error", "raw": result_text}
            
        # Save to notes file (JSONL format)
        note = {
            "timestamp": datetime.now().isoformat(),
            "chunk": chunk_text[:200],  # First 200 chars for reference
            "analysis": result
        }
        with open(self.notes_file, 'a') as f:
            f.write(json.dumps(note) + '\n')
            
        # Accumulate
        self._accumulate(result)
        
        return result
        
    def _accumulate(self, result: Dict):
        """Accumulate findings across chunks."""
        if 'entities' in result:
            self.all_entities.extend(result['entities'])
        if 'action_items' in result:
            self.all_action_items.extend(result['action_items'])
        if 'automation_candidates' in result:
            self.all_automations.extend(result['automation_candidates'])
        if 'preferences_detected' in result:
            self.all_preferences.extend(result['preferences_detected'])
            
    def save_session_summary(self) -> Dict:
        """Save accumulated findings to files."""
        # Deduplicate entities
        unique_entities = self._dedupe_entities()
        
        # Filter automations by confidence
        high_confidence_automations = [
            a for a in self.all_automations if a.get('confidence', 0) > 0.5
        ]
        
        summary = {
            "session_dir": str(self.session_dir),
            "timestamp": datetime.now().isoformat(),
            "entities": unique_entities,
            "action_items": list(set(self.all_action_items)),
            "automations": high_confidence_automations,
            "preferences": self.all_preferences
        }
        
        # Save entities
        with open(self.entities_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        return summary
        
    def _dedupe_entities(self) -> List[Dict]:
        """Remove duplicate entities."""
        seen = set()
        unique = []
        for entity in self.all_entities:
            key = (entity.get('type'), entity.get('value'))
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        return unique
```

**Acceptance Criteria:**
- [ ] Chunks analyzed in <5s each
- [ ] Valid JSON output
- [ ] Entities tracked across session
- [ ] Notes saved in JSONL format

---

### P7-03: Post-Session Processing — 2h

**Goal:** Batch processing after conversation ends

**Post-Processor:**
```python
#!/usr/bin/env python3
# secretary/post_processor.py

import json
import httpx
from pathlib import Path
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434"

class PostSessionProcessor:
    """Clean up and enhance session data after conversation ends."""
    
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.raw_transcript = session_dir / "live_transcript.txt"
        self.clean_transcript = session_dir / "clean_transcript.txt"
        self.session_summary = session_dir / "session_summary.json"
        
    def process(self) -> Dict[str, Any]:
        """Run all post-session processing."""
        print(f"Post-processing: {self.session_dir}")
        
        # Step 1: Clean transcript
        clean_text = self._clean_transcript()
        
        # Step 2: Generate session summary
        summary = self._generate_summary(clean_text)
        
        # Step 3: Extract structured data
        structured = self._extract_structured_data(clean_text)
        
        # Step 4: Identify automation suggestions
        automations = self._suggest_automations(clean_text, structured)
        
        # Combine results
        result = {
            "session_dir": str(self.session_dir),
            "processed_at": datetime.now().isoformat(),
            "summary": summary,
            "word_count": len(clean_text.split()),
            "duration_estimate_minutes": len(clean_text.split()) / 150,
            "entities": structured.get("entities", []),
            "action_items": structured.get("action_items", []),
            "automation_suggestions": automations,
            "topics": structured.get("topics", [])
        }
        
        # Save
        with open(self.session_summary, 'w') as f:
            json.dump(result, f, indent=2)
            
        print(f"Post-processing complete: {self.session_summary}")
        return result
        
    def _clean_transcript(self) -> str:
        """Clean up raw transcript (remove filler, fix punctuation)."""
        with open(self.raw_transcript, 'r') as f:
            raw = f.read()
            
        # Use LLM to clean
        prompt = f"""Clean this transcript. Remove filler words (um, uh), fix punctuation and capitalization. Preserve meaning exactly.

Input:
{raw}

Output clean transcript:"""

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "llama3.1:8b", "prompt": prompt, "stream": False},
            timeout=60.0
        )
        clean = response.json().get("response", raw)
        
        with open(self.clean_transcript, 'w') as f:
            f.write(clean)
            
        return clean
        
    def _generate_summary(self, text: str) -> str:
        """Generate 2-3 sentence summary."""
        prompt = f"""Summarize this conversation in 2-3 sentences:

{text}

Summary:"""

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "llama3.1:8b", "prompt": prompt, "stream": False},
            timeout=30.0
        )
        return response.json().get("response", "")
        
    def _extract_structured_data(self, text: str) -> Dict:
        """Extract entities, action items, topics."""
        prompt = f"""Extract structured data from this conversation. Output JSON only.

Conversation:
{text}

JSON format:
{{"entities": [...], "action_items": [...], "topics": [...]}}"""

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "secretary", "prompt": prompt, "stream": False},
            timeout=30.0
        )
        
        try:
            return json.loads(response.json().get("response", "{}"))
        except:
            return {}
            
    def _suggest_automations(self, text: str, structured: Dict) -> list:
        """Suggest automations based on patterns."""
        prompt = f"""Based on this conversation and extracted data, suggest smart home automations.

Conversation topics: {structured.get('topics', [])}
Entities mentioned: {structured.get('entities', [])}

Suggest automations that would help this household. Output JSON array:
[{{"name": "...", "trigger": "...", "action": "...", "rationale": "..."}}]"""

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "secretary", "prompt": prompt, "stream": False},
            timeout=30.0
        )
        
        try:
            return json.loads(response.json().get("response", "[]"))
        except:
            return []
```

**Acceptance Criteria:**
- [ ] Raw transcript cleaned
- [ ] Summary generated
- [ ] Entities and topics extracted
- [ ] Automation suggestions provided

---

### P7-04: Memory Extraction — 2h

**Goal:** Extract long-term knowledge to structured state/vector memory

**Memory Extractor:**
```python
#!/usr/bin/env python3
# secretary/memory_extractor.py

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class MemoryExtractor:
    """Extract and store long-term memories from sessions."""
    
    def __init__(self, memory_dir: str = "~/hub_memory"):
        self.memory_dir = Path(memory_dir).expanduser()
        self.state_file = self.memory_dir / "structured_state.json"
        self.preferences_file = self.memory_dir / "user_preferences.json"
        self.entities_file = self.memory_dir / "known_entities.json"
        
        # Ensure directory exists
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self.structured_state = self._load_json(self.state_file, {})
        self.preferences = self._load_json(self.preferences_file, {"users": {}})
        self.entities = self._load_json(self.entities_file, {"people": [], "places": [], "products": []})
        
    def _load_json(self, path: Path, default: dict) -> dict:
        """Load JSON file or return default."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return default
            
    def _save_json(self, path: Path, data: dict):
        """Save data to JSON file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def extract_from_session(self, session_summary: Dict) -> Dict[str, int]:
        """Extract memories from a session summary."""
        stats = {
            "preferences_added": 0,
            "entities_added": 0,
            "state_updated": 0
        }
        
        # Extract preferences
        if "preferences" in session_summary:
            for pref in session_summary["preferences"]:
                self._add_preference(pref)
                stats["preferences_added"] += 1
                
        # Extract entities
        if "entities" in session_summary:
            for entity in session_summary["entities"]:
                if self._add_entity(entity):
                    stats["entities_added"] += 1
                    
        # Update structured state
        if "action_items" in session_summary:
            self._update_state("pending_todos", session_summary["action_items"])
            stats["state_updated"] += 1
            
        # Save all
        self._save_json(self.state_file, self.structured_state)
        self._save_json(self.preferences_file, self.preferences)
        self._save_json(self.entities_file, self.entities)
        
        return stats
        
    def _add_preference(self, pref: Dict):
        """Add a user preference."""
        user = pref.get("user", "default")
        category = pref.get("category", "general")
        
        if user not in self.preferences["users"]:
            self.preferences["users"][user] = {}
            
        if category not in self.preferences["users"][user]:
            self.preferences["users"][user][category] = []
            
        # Add with timestamp
        self.preferences["users"][user][category].append({
            "preference": pref.get("preference"),
            "source": pref.get("source_quote"),
            "added": datetime.now().isoformat()
        })
        
    def _add_entity(self, entity: Dict) -> bool:
        """Add entity if not duplicate."""
        entity_type = entity.get("type", "other")
        value = entity.get("value", "")
        
        if entity_type not in self.entities:
            self.entities[entity_type] = []
            
        # Check for duplicate
        existing = [e.get("value") for e in self.entities[entity_type]]
        if value not in existing:
            self.entities[entity_type].append({
                "value": value,
                "first_seen": datetime.now().isoformat()
            })
            return True
        return False
        
    def _update_state(self, key: str, values: List):
        """Update structured state."""
        if key not in self.structured_state:
            self.structured_state[key] = []
            
        # Add new items with timestamps
        for value in values:
            self.structured_state[key].append({
                "value": value,
                "added": datetime.now().isoformat(),
                "status": "pending"
            })
```

**Acceptance Criteria:**
- [ ] Preferences extracted and stored
- [ ] Entities deduplicated and stored
- [ ] Action items tracked in state
- [ ] JSON files persistently updated

---

### P7-05: Archival System — 2h

**Goal:** Compress and index old sessions

**Archival Service:**
```python
#!/usr/bin/env python3
# secretary/archival.py

import os
import gzip
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

class ArchivalService:
    """Compress and index old sessions."""
    
    def __init__(
        self,
        sessions_dir: str = "~/hub_sessions",
        archive_dir: str = "~/hub_archive",
        retention_days: int = 30
    ):
        self.sessions_dir = Path(sessions_dir).expanduser()
        self.archive_dir = Path(archive_dir).expanduser()
        self.retention_days = retention_days
        
        # Create archive dir
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file
        self.index_file = self.archive_dir / "archive_index.json"
        
    def run_archival(self) -> Dict[str, int]:
        """Archive sessions older than retention_days."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        stats = {
            "sessions_archived": 0,
            "bytes_before": 0,
            "bytes_after": 0
        }
        
        # Find old sessions
        for year_dir in self.sessions_dir.iterdir():
            if not year_dir.is_dir():
                continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    for session_dir in day_dir.iterdir():
                        if not session_dir.is_dir():
                            continue
                        # Check if old enough
                        session_date = self._parse_session_date(session_dir.name)
                        if session_date and session_date < cutoff:
                            result = self._archive_session(session_dir)
                            stats["sessions_archived"] += 1
                            stats["bytes_before"] += result["before"]
                            stats["bytes_after"] += result["after"]
                            
        return stats
        
    def _parse_session_date(self, name: str) -> datetime | None:
        """Parse session_YYYYMMDD_HHMMSS format."""
        try:
            parts = name.replace("session_", "")
            return datetime.strptime(parts, "%Y%m%d_%H%M%S")
        except:
            return None
            
    def _archive_session(self, session_dir: Path) -> Dict[str, int]:
        """Archive a single session."""
        # Calculate size before
        size_before = self._dir_size(session_dir)
        
        # Create archive path
        archive_name = f"{session_dir.name}.tar.gz"
        archive_path = self.archive_dir / archive_name
        
        # Compress
        shutil.make_archive(
            str(archive_path.with_suffix('')),  # Base name without .tar.gz
            'gztar',
            session_dir.parent,
            session_dir.name
        )
        
        size_after = archive_path.stat().st_size
        
        # Update index
        self._update_index(session_dir, archive_path)
        
        # Remove original
        shutil.rmtree(session_dir)
        
        return {"before": size_before, "after": size_after}
        
    def _dir_size(self, path: Path) -> int:
        """Calculate total directory size."""
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        
    def _update_index(self, session_dir: Path, archive_path: Path):
        """Update archive index."""
        # Load existing index
        index = self._load_json(self.index_file, {"sessions": []})
        
        # Load session summary if exists
        summary_file = session_dir / "session_summary.json"
        summary = self._load_json(summary_file, {})
        
        # Add to index
        index["sessions"].append({
            "session_name": session_dir.name,
            "archive_path": str(archive_path),
            "archived_at": datetime.now().isoformat(),
            "summary": summary.get("summary", ""),
            "topics": summary.get("topics", []),
            "word_count": summary.get("word_count", 0)
        })
        
        # Save index
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=2)
            
    def _load_json(self, path: Path, default: dict) -> dict:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return default
            
    def search_archive(self, query: str) -> List[Dict]:
        """Search archive index for matching sessions."""
        index = self._load_json(self.index_file, {"sessions": []})
        
        results = []
        query_lower = query.lower()
        
        for session in index["sessions"]:
            # Search in summary and topics
            if query_lower in session.get("summary", "").lower():
                results.append(session)
            elif any(query_lower in t.lower() for t in session.get("topics", [])):
                results.append(session)
                
        return results
```

**Acceptance Criteria:**
- [ ] Sessions older than 30 days archived
- [ ] Compression reduces size by >50%
- [ ] Index searchable by topics/summary
- [ ] Original files removed after archive

---

### P7-06: Automation Hooks — 2h

**Goal:** Create Home Assistant automations from suggestions

**Automation Creator:**
```python
#!/usr/bin/env python3
# secretary/automation_hooks.py

import json
import httpx
from typing import Dict, List, Any

HA_BASE = "http://homeassistant.local:8123"

class AutomationCreator:
    """Create Home Assistant automations from Secretary suggestions."""
    
    def __init__(self, ha_token: str):
        self.headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json"
        }
        
    def create_automation(self, suggestion: Dict) -> Dict[str, Any]:
        """
        Create an automation from a Secretary suggestion.
        
        suggestion format:
        {
            "name": "Turn off lights at bedtime",
            "trigger": "time: 22:00",
            "action": "turn_off light.bedroom",
            "rationale": "User mentioned going to bed at 10pm"
        }
        """
        # Convert natural language to HA automation format
        automation = self._convert_to_ha_format(suggestion)
        
        # Submit to HA as a "draft" automation (disabled by default)
        automation["enabled"] = False
        automation["description"] = f"[Secretary Draft] {suggestion.get('rationale', '')}"
        
        # Create via HA API
        response = httpx.post(
            f"{HA_BASE}/api/config/automation/config/{automation['id']}",
            headers=self.headers,
            json=automation,
            timeout=10.0
        )
        
        if response.status_code == 200:
            return {"status": "created", "automation_id": automation["id"]}
        else:
            return {"status": "error", "message": response.text}
            
    def _convert_to_ha_format(self, suggestion: Dict) -> Dict:
        """Convert natural language suggestion to HA automation format."""
        # Parse trigger
        trigger = self._parse_trigger(suggestion.get("trigger", ""))
        
        # Parse action
        action = self._parse_action(suggestion.get("action", ""))
        
        # Generate unique ID
        import hashlib
        automation_id = hashlib.md5(
            suggestion.get("name", "").encode()
        ).hexdigest()[:8]
        
        return {
            "id": f"secretary_{automation_id}",
            "alias": f"[Secretary] {suggestion.get('name', 'Unnamed')}",
            "trigger": [trigger],
            "action": [action],
            "mode": "single"
        }
        
    def _parse_trigger(self, trigger_text: str) -> Dict:
        """Parse natural language trigger to HA format."""
        trigger_text = trigger_text.lower()
        
        # Time-based triggers
        if "time:" in trigger_text:
            time_str = trigger_text.replace("time:", "").strip()
            return {"platform": "time", "at": time_str}
            
        # State-based triggers
        if "when" in trigger_text and "turns" in trigger_text:
            # "when light.living_room turns on"
            parts = trigger_text.split()
            entity = next((p for p in parts if '.' in p), "")
            state = "on" if "on" in trigger_text else "off"
            return {
                "platform": "state",
                "entity_id": entity,
                "to": state
            }
            
        # Default: manual trigger
        return {"platform": "event", "event_type": "manual_trigger"}
        
    def _parse_action(self, action_text: str) -> Dict:
        """Parse natural language action to HA format."""
        action_text = action_text.lower()
        
        # Turn on/off
        if "turn_on" in action_text or "turn on" in action_text:
            parts = action_text.split()
            entity = next((p for p in parts if '.' in p), "")
            return {"service": "homeassistant.turn_on", "target": {"entity_id": entity}}
            
        if "turn_off" in action_text or "turn off" in action_text:
            parts = action_text.split()
            entity = next((p for p in parts if '.' in p), "")
            return {"service": "homeassistant.turn_off", "target": {"entity_id": entity}}
            
        # Default: notification
        return {
            "service": "notify.notify",
            "data": {"message": f"Secretary automation: {action_text}"}
        }
        
    def get_pending_drafts(self) -> List[Dict]:
        """Get all Secretary draft automations pending review."""
        response = httpx.get(
            f"{HA_BASE}/api/config/automation/config",
            headers=self.headers,
            timeout=10.0
        )
        
        automations = response.json()
        return [
            a for a in automations 
            if a.get("id", "").startswith("secretary_") and not a.get("enabled", True)
        ]
```

**User Review Flow:**
```python
# secretary/review_automations.py

def send_for_review(automation: Dict, creator: AutomationCreator):
    """Send draft automation for user review via HA notification."""
    httpx.post(
        f"{HA_BASE}/api/services/notify/notify",
        headers=creator.headers,
        json={
            "title": "Secretary Automation Suggestion",
            "message": f"""
New automation ready for review:
📋 {automation['name']}
🎯 Trigger: {automation['trigger']}
⚡ Action: {automation['action']}
💡 Reason: {automation['rationale']}

Tap to review and enable in Home Assistant.
""",
            "data": {
                "url": f"/config/automation/edit/{automation['id']}",
                "tag": "secretary_automation"
            }
        }
    )
```

**Acceptance Criteria:**
- [ ] Suggestions converted to HA automation format
- [ ] Automations created as disabled drafts
- [ ] User notified of pending review
- [ ] Review dashboard accessible

---

### P7-07: Secretary Testing — 2h

**Goal:** Comprehensive tests for Secretary pipeline

**Test Suite:**
```python
#!/usr/bin/env python3
# test_secretary.py

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from secretary.live_transcript import LiveTranscriptService, ChunkedTranscriptProcessor
from secretary.live_engine import LiveSecretaryEngine
from secretary.post_processor import PostSessionProcessor
from secretary.memory_extractor import MemoryExtractor
from secretary.archival import ArchivalService
from secretary.automation_hooks import AutomationCreator


class TestLiveTranscription:
    def test_session_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = LiveTranscriptService(output_dir=tmpdir)
            session_dir = service.start_session()
            
            assert session_dir.exists()
            assert "session_" in session_dir.name
            
            service.stop_session()
            

class TestChunkedProcessor:
    def test_yields_new_chunks(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Write ~300 words (2 chunks)
            f.write(" ".join(["word"] * 300))
            f.flush()
            
            processor = ChunkedTranscriptProcessor(Path(f.name))
            chunks = list(processor.get_new_chunks())
            
            assert len(chunks) == 2
            

class TestLiveEngine:
    @patch('secretary.live_engine.httpx.post')
    def test_processes_chunk(self, mock_post):
        mock_post.return_value.json.return_value = {
            "response": json.dumps({
                "summary": "Test chunk",
                "entities": [{"type": "person", "value": "Alex"}],
                "action_items": [],
                "automation_candidates": [],
                "preferences_detected": []
            })
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = LiveSecretaryEngine(Path(tmpdir))
            result = engine.process_chunk("Hello, this is Alex speaking.")
            
            assert result["summary"] == "Test chunk"
            assert len(result["entities"]) == 1
            

class TestMemoryExtractor:
    def test_adds_new_entity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = MemoryExtractor(memory_dir=tmpdir)
            
            summary = {
                "entities": [{"type": "person", "value": "Alice"}],
                "preferences": []
            }
            
            stats = extractor.extract_from_session(summary)
            
            assert stats["entities_added"] == 1
            assert "Alice" in [e["value"] for e in extractor.entities["person"]]
            
    def test_deduplicates_entities(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = MemoryExtractor(memory_dir=tmpdir)
            
            # Add same entity twice
            for _ in range(2):
                extractor.extract_from_session({
                    "entities": [{"type": "person", "value": "Bob"}]
                })
                
            assert len(extractor.entities["person"]) == 1


class TestArchival:
    def test_compresses_old_session(self):
        with tempfile.TemporaryDirectory() as sessions_dir:
            with tempfile.TemporaryDirectory() as archive_dir:
                # Create old session structure
                old_date = "20240101_120000"  # Old date
                session_path = Path(sessions_dir) / "2024" / "01" / "01" / f"session_{old_date}"
                session_path.mkdir(parents=True)
                (session_path / "transcript.txt").write_text("Test content")
                
                archiver = ArchivalService(
                    sessions_dir=sessions_dir,
                    archive_dir=archive_dir,
                    retention_days=0  # Archive everything
                )
                
                stats = archiver.run_archival()
                
                assert stats["sessions_archived"] == 1
                assert not session_path.exists()
                assert (Path(archive_dir) / f"session_{old_date}.tar.gz").exists()


class TestAutomationHooks:
    def test_parses_time_trigger(self):
        creator = AutomationCreator("fake_token")
        trigger = creator._parse_trigger("time: 22:00")
        
        assert trigger["platform"] == "time"
        assert trigger["at"] == "22:00"
        
    def test_parses_turn_off_action(self):
        creator = AutomationCreator("fake_token")
        action = creator._parse_action("turn_off light.bedroom")
        
        assert action["service"] == "homeassistant.turn_off"
        assert action["target"]["entity_id"] == "light.bedroom"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] Live transcription tested
- [ ] Engine output validated
- [ ] Memory persistence tested
- [ ] Archival compression verified
- [ ] Automation parsing correct

---

## 🧪 Validation Commands

```bash
# 1. Build Secretary Modelfile
ollama create secretary -f Modelfile.secretary

# 2. Test live transcription (10 seconds)
python -c "
from secretary.live_transcript import LiveTranscriptService
s = LiveTranscriptService()
s.start_session()
import time; time.sleep(10)
s.stop_session()
"

# 3. Test engine with sample chunk
python -c "
from secretary.live_engine import LiveSecretaryEngine
from pathlib import Path
import tempfile
with tempfile.TemporaryDirectory() as d:
    e = LiveSecretaryEngine(Path(d))
    print(e.process_chunk('Alex said he wants to turn on the lights at 10pm every night.'))
"

# 4. Run full test suite
pytest test_secretary.py -v

# 5. Integration test (5 minute session)
python secretary/live_transcript.py &
sleep 300
pkill -f live_transcript
python secretary/post_processor.py ~/hub_sessions/*/latest/
```

---

## ✅ Definition of Done

- [ ] Live transcription service working
- [ ] Secretary Modelfile built and tested
- [ ] Live engine processes chunks in <5s
- [ ] Post-session processing completes
- [ ] Memory extraction persists data
- [ ] Archival compresses old sessions
- [ ] Automation hooks create HA drafts
- [ ] All tests pass
- [ ] 30-minute ambient listening test successful

---

## 📁 Files to Create

| File | Purpose |
|------|---------|
| `Smart_Home/secretary/live_transcript.py` | Continuous transcription |
| `Smart_Home/secretary/live_engine.py` | Real-time chunk analysis |
| `Smart_Home/secretary/post_processor.py` | Post-session cleanup |
| `Smart_Home/secretary/memory_extractor.py` | Long-term memory |
| `Smart_Home/secretary/archival.py` | Compression & indexing |
| `Smart_Home/secretary/automation_hooks.py` | HA automation creation |
| `Smart_Home/secretary/review_automations.py` | User review flow |
| `Smart_Home/Modelfile.secretary` | Secretary personality |
| `Smart_Home/tests/test_secretary.py` | Test suite |

---

## 🔗 Dependencies

**Python:**
```
httpx>=0.24.0
pydantic>=2.0.0
```

**Ollama:**
```bash
ollama create secretary -f Modelfile.secretary
```

**From Issue #1:**
- HA API access pattern (ha_client.py)

---

**END OF HANDOFF**
