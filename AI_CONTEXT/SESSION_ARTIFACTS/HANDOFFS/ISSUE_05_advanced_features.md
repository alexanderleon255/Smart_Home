# [Background Agent] Issue #5: Advanced Features

**Roadmap Items:** P8-01, P8-02, P8-03, P8-04, P8-05, P8-06  
**Estimated Effort:** 12-15h total  
**Estimated LOC:** ~350  
**Priority:** LOW (enhancement features)  
**Dependencies:** Issue #1 (HA client pattern) AND Issue #4 (session data for vector memory)  
**Parallel Track:** WAVE 2 — Start after Issues #1 and #4 complete

---

## 🎯 Objective

Implement advanced "Phase 8" features that enhance the smart home system with long-term memory, periodic summaries, voice satellite support, AI camera integration, and behavioral pattern learning.

---

## 📚 Context to Load

**Required Reading:**
- `Smart_Home/AI_CONTEXT/SOURCES/vision_document.md` — §5.6 (Memory Tiers), §13 (Success Criteria)
- `Smart_Home/References/Secretary_Ambient_Architecture_v1.0.md` — Memory architecture
- `Smart_Home/References/Explicit_Interface_Contracts_v1.0.md` — §4 (Memory Layer: vector memory contract, structured state schema)

**System State (from prior issues):**
- Tool Broker operational (Issue #1) — provides HA client pattern
- Secretary pipeline collecting data (Issue #4) — provides session data for vector memory

**Why WAVE 2:** This issue uses HA client patterns from Issue #1 and indexes session data from Issue #4. Does NOT require voice loop (Issues #2, #3).

**Memory Architecture:**
```
TIER 1: Ephemeral (per-session)
  └── Conversation context, recent commands

TIER 2: Structured State (persistent JSON)
  └── User preferences, device states, todos

TIER 3: Event Log (append-only SQLite)
  └── All commands, outcomes, timestamps

TIER 4: Vector Memory (RAG-ready)
  └── Semantic search of historical data
```

---

## 📋 Detailed Tasks

### P8-01: Vector Memory Integration — 3h

**Goal:** Semantic search over historical conversations and notes

**ChromaDB Setup:**
```bash
pip install chromadb sentence-transformers
```

**Vector Memory Implementation:**
```python
#!/usr/bin/env python3
# memory/vector_store.py

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class VectorMemory:
    """Semantic search over historical data using ChromaDB."""
    
    def __init__(
        self,
        persist_dir: str = "~/hub_memory/vector_db",
        model_name: str = "all-MiniLM-L6-v2"  # Fast, small model
    ):
        self.persist_dir = Path(persist_dir).expanduser()
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(self.persist_dir),
            anonymized_telemetry=False
        ))
        
        # Collections
        self.conversations = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Session transcripts and summaries"}
        )
        self.entities = self.client.get_or_create_collection(
            name="entities",
            metadata={"description": "People, places, products mentioned"}
        )
        self.automations = self.client.get_or_create_collection(
            name="automations",
            metadata={"description": "Created automations and their rationale"}
        )
        
        # Embedding model
        self.embedder = SentenceTransformer(model_name)
        
    def add_conversation(
        self,
        text: str,
        metadata: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """Add conversation chunk or summary to vector store."""
        if session_id is None:
            session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
            
        embedding = self.embedder.encode(text).tolist()
        
        self.conversations.add(
            ids=[f"{session_id}_{hash(text) % 10000}"],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                **metadata,
                "session_id": session_id,
                "indexed_at": datetime.now().isoformat()
            }]
        )
        
    def add_entity(
        self,
        entity_type: str,
        entity_value: str,
        context: str,
        source_session: str
    ):
        """Add entity with context to vector store."""
        text = f"{entity_type}: {entity_value}. Context: {context}"
        embedding = self.embedder.encode(text).tolist()
        
        self.entities.add(
            ids=[f"entity_{hash(text) % 100000}"],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "type": entity_type,
                "value": entity_value,
                "context": context,
                "source_session": source_session,
                "indexed_at": datetime.now().isoformat()
            }]
        )
        
    def search(
        self,
        query: str,
        collection: str = "conversations",
        n_results: int = 5
    ) -> List[Dict]:
        """Semantic search across a collection."""
        collection_obj = getattr(self, collection)
        query_embedding = self.embedder.encode(query).tolist()
        
        results = collection_obj.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
            })
            
        return formatted
        
    def search_all(self, query: str, n_results: int = 5) -> Dict[str, List[Dict]]:
        """Search across all collections."""
        return {
            "conversations": self.search(query, "conversations", n_results),
            "entities": self.search(query, "entities", n_results),
            "automations": self.search(query, "automations", n_results)
        }
        
    def get_stats(self) -> Dict[str, int]:
        """Get collection sizes."""
        return {
            "conversations": self.conversations.count(),
            "entities": self.entities.count(),
            "automations": self.automations.count()
        }
```

**Integration with Jarvis:**
```python
# Add to tool_broker/main.py

from memory.vector_store import VectorMemory

vector_memory = VectorMemory()

def enhance_prompt_with_memory(user_query: str) -> str:
    """Add relevant memories to query context."""
    memories = vector_memory.search(user_query, n_results=3)
    
    if not memories:
        return user_query
        
    context = "\n".join([
        f"- {m['document'][:200]}..." for m in memories
    ])
    
    return f"""Relevant context from memory:
{context}

Current query: {user_query}"""
```

**Acceptance Criteria:**
- [ ] ChromaDB persists to disk
- [ ] Conversations indexed on session end
- [ ] Entities indexed with context
- [ ] Search returns relevant results
- [ ] Integration with Jarvis queries

---

### P8-02: Daily Digest Generation — 2h

**Goal:** Morning summary of previous day

**Digest Generator:**
```python
#!/usr/bin/env python3
# digests/daily_digest.py

import json
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

OLLAMA_URL = "http://localhost:11434"
HA_BASE = "http://homeassistant.local:8123"

class DailyDigestGenerator:
    """Generate morning digest of previous day's activity."""
    
    def __init__(
        self,
        sessions_dir: str = "~/hub_sessions",
        digests_dir: str = "~/hub_memory/digests",
        ha_token: str = ""
    ):
        self.sessions_dir = Path(sessions_dir).expanduser()
        self.digests_dir = Path(digests_dir).expanduser()
        self.digests_dir.mkdir(parents=True, exist_ok=True)
        self.ha_token = ha_token
        
    def generate_digest(self, date: datetime = None) -> Dict[str, Any]:
        """Generate digest for a specific date (default: yesterday)."""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        date_str = date.strftime("%Y-%m-%d")
        print(f"Generating digest for {date_str}")
        
        # Collect data
        sessions = self._get_sessions_for_date(date)
        commands = self._get_commands_for_date(date)
        automations = self._get_automation_runs(date)
        
        # Generate digest with LLM
        digest_text = self._generate_llm_digest(
            date_str, sessions, commands, automations
        )
        
        # Build digest object
        digest = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "summary": digest_text,
            "stats": {
                "sessions_count": len(sessions),
                "commands_count": len(commands),
                "automations_count": len(automations)
            },
            "sessions": sessions,
            "notable_commands": commands[:10],
            "automation_highlights": automations[:5]
        }
        
        # Save digest
        digest_file = self.digests_dir / f"daily_{date_str}.json"
        with open(digest_file, 'w') as f:
            json.dump(digest, f, indent=2)
            
        # Also save readable version
        readable_file = self.digests_dir / f"daily_{date_str}.md"
        with open(readable_file, 'w') as f:
            f.write(self._format_markdown(digest))
            
        return digest
        
    def _get_sessions_for_date(self, date: datetime) -> List[Dict]:
        """Get session summaries for date."""
        date_dir = self.sessions_dir / date.strftime("%Y/%m/%d")
        
        if not date_dir.exists():
            return []
            
        sessions = []
        for session_dir in date_dir.iterdir():
            if not session_dir.is_dir():
                continue
                
            summary_file = session_dir / "session_summary.json"
            if summary_file.exists():
                with open(summary_file) as f:
                    sessions.append(json.load(f))
                    
        return sessions
        
    def _get_commands_for_date(self, date: datetime) -> List[Dict]:
        """Get commands from event log for date."""
        # TODO: Query SQLite event log
        # For now, return placeholder
        return []
        
    def _get_automation_runs(self, date: datetime) -> List[Dict]:
        """Get automation run stats from HA."""
        # Query HA logbook API
        try:
            response = httpx.get(
                f"{HA_BASE}/api/logbook/{date.isoformat()}",
                headers={"Authorization": f"Bearer {self.ha_token}"},
                timeout=10.0
            )
            events = response.json()
            
            # Filter for automation events
            return [
                e for e in events
                if e.get("domain") == "automation"
            ]
        except:
            return []
            
    def _generate_llm_digest(
        self,
        date_str: str,
        sessions: List[Dict],
        commands: List[Dict],
        automations: List[Dict]
    ) -> str:
        """Generate natural language summary."""
        prompt = f"""Generate a brief morning digest for {date_str}.

Sessions (count: {len(sessions)}):
{json.dumps([s.get('summary', '') for s in sessions[:5]], indent=2)}

Commands (count: {len(commands)}):
{json.dumps(commands[:5], indent=2)}

Automations (count: {len(automations)}):
{json.dumps([a.get('name', '') for a in automations[:5]], indent=2)}

Write a 3-5 sentence summary of the day's activity, highlighting:
- Key conversations or interactions
- Most used features
- Any notable patterns

Summary:"""

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "llama3.1:8b", "prompt": prompt, "stream": False},
            timeout=60.0
        )
        
        return response.json().get("response", "No summary generated.")
        
    def _format_markdown(self, digest: Dict) -> str:
        """Format digest as readable Markdown."""
        return f"""# Daily Digest: {digest['date']}

## Summary
{digest['summary']}

## Stats
- 🗣️ Sessions: {digest['stats']['sessions_count']}
- ⚡ Commands: {digest['stats']['commands_count']}
- 🤖 Automations: {digest['stats']['automations_count']}

## Session Highlights
{self._format_session_list(digest['sessions'])}

---
*Generated at {digest['generated_at']}*
"""

    def _format_session_list(self, sessions: List[Dict]) -> str:
        if not sessions:
            return "_No sessions recorded_"
        return "\n".join([
            f"- {s.get('summary', 'No summary')}" for s in sessions[:5]
        ])
        
    def send_notification(self, digest: Dict):
        """Send digest notification via HA."""
        httpx.post(
            f"{HA_BASE}/api/services/notify/notify",
            headers={"Authorization": f"Bearer {self.ha_token}"},
            json={
                "title": f"🌅 Daily Digest: {digest['date']}",
                "message": digest['summary'],
                "data": {
                    "tag": "daily_digest",
                    "url": f"/local/digests/daily_{digest['date']}.md"
                }
            },
            timeout=10.0
        )
```

**Scheduled Execution:**
```python
# Add to HA automation or cron

# Via crontab:
# 0 7 * * * /path/to/python /path/to/daily_digest.py

# Via HA automation:
# trigger:
#   platform: time
#   at: "07:00:00"
# action:
#   service: shell_command.generate_daily_digest
```

**Acceptance Criteria:**
- [ ] Collects all sessions from previous day
- [ ] Generates LLM summary
- [ ] Saves JSON and Markdown versions
- [ ] Sends notification at 7am
- [ ] Runs automatically via cron/HA

---

### P8-03: Weekly Review Generation — 2h

**Goal:** Weekly summary with trends and patterns

**Weekly Review Generator:**
```python
#!/usr/bin/env python3
# digests/weekly_review.py

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import httpx

OLLAMA_URL = "http://localhost:11434"

class WeeklyReviewGenerator:
    """Generate weekly review with trends and patterns."""
    
    def __init__(
        self,
        digests_dir: str = "~/hub_memory/digests",
        memory_dir: str = "~/hub_memory"
    ):
        self.digests_dir = Path(digests_dir).expanduser()
        self.memory_dir = Path(memory_dir).expanduser()
        
    def generate_review(self, end_date: datetime = None) -> Dict:
        """Generate weekly review ending on end_date."""
        if end_date is None:
            end_date = datetime.now()
            
        start_date = end_date - timedelta(days=7)
        
        # Collect daily digests
        daily_digests = self._collect_digests(start_date, end_date)
        
        # Analyze patterns
        patterns = self._analyze_patterns(daily_digests)
        
        # Identify trends
        trends = self._identify_trends(daily_digests)
        
        # Generate review with LLM
        review_text = self._generate_llm_review(
            start_date, end_date, daily_digests, patterns, trends
        )
        
        # Build review object
        review = {
            "week_start": start_date.strftime("%Y-%m-%d"),
            "week_end": end_date.strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "summary": review_text,
            "stats": {
                "total_sessions": sum(d['stats']['sessions_count'] for d in daily_digests),
                "total_commands": sum(d['stats']['commands_count'] for d in daily_digests),
                "total_automations": sum(d['stats']['automations_count'] for d in daily_digests)
            },
            "patterns": patterns,
            "trends": trends,
            "recommendations": self._generate_recommendations(patterns, trends)
        }
        
        # Save
        week_str = start_date.strftime("%Y-W%W")
        review_file = self.digests_dir / f"weekly_{week_str}.json"
        with open(review_file, 'w') as f:
            json.dump(review, f, indent=2)
            
        return review
        
    def _collect_digests(self, start: datetime, end: datetime) -> List[Dict]:
        """Collect daily digests for date range."""
        digests = []
        current = start
        
        while current <= end:
            digest_file = self.digests_dir / f"daily_{current.strftime('%Y-%m-%d')}.json"
            if digest_file.exists():
                with open(digest_file) as f:
                    digests.append(json.load(f))
            current += timedelta(days=1)
            
        return digests
        
    def _analyze_patterns(self, digests: List[Dict]) -> List[Dict]:
        """Identify recurring patterns in the week's data."""
        # TODO: More sophisticated pattern analysis
        patterns = []
        
        # Simple: count most active days
        activity_by_day = {
            d['date']: d['stats']['sessions_count'] for d in digests
        }
        
        if activity_by_day:
            most_active = max(activity_by_day.items(), key=lambda x: x[1])
            patterns.append({
                "type": "activity",
                "description": f"Most active day: {most_active[0]} ({most_active[1]} sessions)"
            })
            
        return patterns
        
    def _identify_trends(self, digests: List[Dict]) -> List[Dict]:
        """Identify trends over the week."""
        if len(digests) < 2:
            return []
            
        trends = []
        
        # Compare first half vs second half
        mid = len(digests) // 2
        first_half = sum(d['stats']['sessions_count'] for d in digests[:mid])
        second_half = sum(d['stats']['sessions_count'] for d in digests[mid:])
        
        if second_half > first_half * 1.2:
            trends.append({
                "type": "increasing",
                "metric": "sessions",
                "description": "Usage increased toward end of week"
            })
        elif first_half > second_half * 1.2:
            trends.append({
                "type": "decreasing",
                "metric": "sessions",
                "description": "Usage decreased toward end of week"
            })
            
        return trends
        
    def _generate_llm_review(
        self,
        start: datetime,
        end: datetime,
        digests: List[Dict],
        patterns: List[Dict],
        trends: List[Dict]
    ) -> str:
        """Generate natural language weekly review."""
        prompt = f"""Generate a weekly review for {start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}.

Daily summaries:
{json.dumps([d['summary'] for d in digests], indent=2)}

Patterns detected:
{json.dumps(patterns, indent=2)}

Trends:
{json.dumps(trends, indent=2)}

Write a thoughtful 5-7 sentence weekly review that:
- Summarizes the week's smart home activity
- Highlights any interesting patterns
- Notes what worked well
- Suggests improvements for next week

Weekly Review:"""

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "llama3.1:8b", "prompt": prompt, "stream": False},
            timeout=120.0
        )
        
        return response.json().get("response", "")
        
    def _generate_recommendations(
        self,
        patterns: List[Dict],
        trends: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations."""
        # TODO: More sophisticated recommendation logic
        recommendations = []
        
        for trend in trends:
            if trend['type'] == 'decreasing':
                recommendations.append(
                    "Consider reviewing if automations are meeting needs"
                )
                
        return recommendations
```

**Acceptance Criteria:**
- [ ] Aggregates 7 days of daily digests
- [ ] Identifies patterns and trends
- [ ] Generates comprehensive review
- [ ] Provides recommendations
- [ ] Runs every Sunday night

---

### P8-04: Voice Satellite Support — 2h

**Goal:** Additional microphone endpoints around the house

**Satellite Architecture:**
```
SATELLITE (ESP32/Pi Zero W)
    └── Wake word detection (local)
    └── Audio streaming to hub

HUB (Mac M1)
    └── Receives audio from any satellite
    └── Routes to Jarvis for processing
    └── Routes TTS back to originating satellite
```

**Satellite Discovery Service:**
```python
#!/usr/bin/env python3
# satellites/discovery.py

import socket
import json
import threading
from typing import Dict, List

class SatelliteDiscoveryService:
    """Discover and manage voice satellites on the network."""
    
    DISCOVERY_PORT = 5380
    
    def __init__(self):
        self.satellites: Dict[str, Dict] = {}
        self._running = False
        
    def start(self):
        """Start discovery listener."""
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop)
        self._thread.start()
        
    def stop(self):
        """Stop discovery listener."""
        self._running = False
        if hasattr(self, '_thread'):
            self._thread.join()
            
    def _listen_loop(self):
        """Listen for satellite announcements."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.DISCOVERY_PORT))
        sock.settimeout(1.0)
        
        while self._running:
            try:
                data, addr = sock.recvfrom(1024)
                announcement = json.loads(data.decode())
                
                satellite_id = announcement.get('id')
                if satellite_id:
                    self.satellites[satellite_id] = {
                        **announcement,
                        'ip': addr[0],
                        'last_seen': time.time()
                    }
                    print(f"Satellite discovered: {satellite_id} at {addr[0]}")
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Discovery error: {e}")
                
    def get_active_satellites(self) -> List[Dict]:
        """Get list of active satellites."""
        now = time.time()
        return [
            s for s in self.satellites.values()
            if now - s['last_seen'] < 60  # Active within last minute
        ]


class SatelliteAudioRouter:
    """Route audio streams from satellites."""
    
    def __init__(self, voice_loop):
        self.voice_loop = voice_loop
        self.active_satellite = None
        
    def handle_wake_from_satellite(self, satellite_id: str, audio_stream):
        """Handle wake word detection from a satellite."""
        print(f"Wake from satellite: {satellite_id}")
        self.active_satellite = satellite_id
        
        # Route audio to voice loop
        self.voice_loop.set_audio_input(audio_stream)
        self.voice_loop._transition_to(VoiceState.ATTENDING)
        
    def route_tts_to_satellite(self, satellite_id: str, audio_data: bytes):
        """Route TTS output to specific satellite."""
        satellite = self.satellites.get(satellite_id)
        if satellite:
            # Stream audio to satellite
            # TODO: Implement audio streaming protocol
            pass
```

**ESP32 Satellite Firmware (Reference):**
```cpp
// satellites/esp32_satellite/main.cpp
// (For reference - implement on ESP32)

#include <WiFi.h>
#include <AudioTools.h>
#include <OpenWakeWord.h>

const char* HUB_IP = "192.168.1.100";  // Mac IP
const int HUB_PORT = 5381;

void setup() {
    // Connect WiFi
    // Initialize I2S microphone
    // Load wake word model
}

void loop() {
    // Read audio samples
    // Run wake word detection
    // If wake word:
    //   - Signal hub
    //   - Stream audio to hub
    // Listen for TTS response from hub
    // Play TTS through speaker
}
```

**Acceptance Criteria:**
- [ ] Satellite discovery via UDP broadcast
- [ ] Audio routing from active satellite
- [ ] TTS routed back to originating satellite
- [ ] Support for multiple concurrent satellites
- [ ] ESP32 firmware reference documented

---

### P8-05: AI Camera Integration — 2h

**Goal:** Process camera events with vision model

**Camera Event Processor:**
```python
#!/usr/bin/env python3
# cameras/event_processor.py

import json
import base64
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

OLLAMA_URL = "http://localhost:11434"

class CameraEventProcessor:
    """Process camera events with vision model."""
    
    def __init__(
        self,
        events_dir: str = "~/hub_memory/camera_events",
        vision_model: str = "llava:7b"  # Or moondream
    ):
        self.events_dir = Path(events_dir).expanduser()
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.vision_model = vision_model
        
    def process_motion_event(
        self,
        camera_id: str,
        image_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process motion detection event."""
        
        # Load image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
            
        # Analyze with vision model
        prompt = """Analyze this security camera image. Describe:
1. What triggered the motion (person, animal, vehicle, other)
2. Number and description of any people visible
3. Any notable objects or activities
4. Potential concerns or noteworthy details

Be concise and factual."""

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": self.vision_model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False
            },
            timeout=120.0
        )
        
        analysis = response.json().get("response", "Analysis failed")
        
        # Build event record
        event = {
            "timestamp": datetime.now().isoformat(),
            "camera_id": camera_id,
            "event_type": "motion",
            "image_path": image_path,
            "analysis": analysis,
            "metadata": metadata,
            "action_taken": None
        }
        
        # Determine if action needed
        if self._requires_action(analysis):
            event["action_taken"] = self._take_action(camera_id, analysis)
            
        # Save event
        self._save_event(event)
        
        return event
        
    def _requires_action(self, analysis: str) -> bool:
        """Determine if analysis requires action."""
        alert_keywords = [
            "person", "human", "someone",
            "package", "delivery",
            "vehicle", "car",
            "door open", "gate open"
        ]
        
        analysis_lower = analysis.lower()
        return any(kw in analysis_lower for kw in alert_keywords)
        
    def _take_action(self, camera_id: str, analysis: str) -> Dict:
        """Take action based on analysis."""
        # Default action: send notification
        # TODO: More sophisticated action routing
        
        return {
            "type": "notification",
            "sent_at": datetime.now().isoformat(),
            "message": f"Camera alert ({camera_id}): {analysis[:100]}..."
        }
        
    def _save_event(self, event: Dict):
        """Save event to file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        events_file = self.events_dir / f"events_{date_str}.jsonl"
        
        with open(events_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
            
    def get_recent_events(self, camera_id: str = None, hours: int = 24) -> List[Dict]:
        """Get recent camera events."""
        events = []
        # TODO: Load from JSONL files
        return events
```

**Integration with Frigate (if used):**
```python
# cameras/frigate_integration.py

import httpx

FRIGATE_URL = "http://frigate.local:5000"

def subscribe_to_frigate_events():
    """Subscribe to Frigate MQTT events."""
    # MQTT subscription to frigate/events
    # On event: call CameraEventProcessor.process_motion_event()
    pass
```

**Acceptance Criteria:**
- [ ] Vision model analyzes camera images
- [ ] Motion events logged with analysis
- [ ] Alerts sent for significant events
- [ ] Integration with Frigate documented
- [ ] Privacy-conscious (local processing)

---

### P8-06: Behavioral Pattern Learning — 2h

**Goal:** Learn and predict user behavior patterns

**Pattern Learner:**
```python
#!/usr/bin/env python3
# patterns/behavioral_learner.py

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

class BehavioralPatternLearner:
    """Learn patterns from user behavior."""
    
    def __init__(
        self,
        patterns_dir: str = "~/hub_memory/patterns"
    ):
        self.patterns_dir = Path(patterns_dir).expanduser()
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        
        # Pattern storage
        self.time_patterns = defaultdict(lambda: defaultdict(int))
        self.sequence_patterns = defaultdict(int)
        self.location_patterns = defaultdict(lambda: defaultdict(int))
        
        self._load_patterns()
        
    def _load_patterns(self):
        """Load existing patterns from disk."""
        patterns_file = self.patterns_dir / "learned_patterns.json"
        if patterns_file.exists():
            with open(patterns_file) as f:
                data = json.load(f)
                # Reconstruct defaultdicts
                # ...
                
    def _save_patterns(self):
        """Save patterns to disk."""
        patterns_file = self.patterns_dir / "learned_patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump({
                "time_patterns": dict(self.time_patterns),
                "sequence_patterns": dict(self.sequence_patterns),
                "location_patterns": dict(self.location_patterns)
            }, f, indent=2)
            
    def observe_action(
        self,
        action: str,
        entity_id: str,
        timestamp: datetime = None
    ):
        """Record an observed action for pattern learning."""
        if timestamp is None:
            timestamp = datetime.now()
            
        # Time-based patterns (hour of day, day of week)
        hour = timestamp.hour
        day = timestamp.strftime("%A")
        
        self.time_patterns[f"{day}_{hour}"][action] += 1
        
        # Save periodically
        self._save_patterns()
        
    def observe_sequence(self, actions: List[str]):
        """Record action sequences."""
        if len(actions) < 2:
            return
            
        # Record 2-grams
        for i in range(len(actions) - 1):
            seq = f"{actions[i]} -> {actions[i+1]}"
            self.sequence_patterns[seq] += 1
            
    def predict_next_action(
        self,
        current_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Predict likely next actions based on patterns."""
        if current_time is None:
            current_time = datetime.now()
            
        hour = current_time.hour
        day = current_time.strftime("%A")
        
        # Get actions common at this time
        time_key = f"{day}_{hour}"
        time_actions = self.time_patterns.get(time_key, {})
        
        # Sort by frequency
        predictions = sorted(
            time_actions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return [
            {"action": action, "confidence": count / max(sum(time_actions.values()), 1)}
            for action, count in predictions
        ]
        
    def suggest_automations(self) -> List[Dict]:
        """Suggest automations based on learned patterns."""
        suggestions = []
        
        # Find high-frequency time patterns
        for time_key, actions in self.time_patterns.items():
            for action, count in actions.items():
                if count >= 5:  # Threshold
                    day, hour = time_key.split('_')
                    suggestions.append({
                        "name": f"Auto-{action} at {hour}:00 on {day}s",
                        "trigger": f"time: {hour}:00",
                        "condition": f"day: {day}",
                        "action": action,
                        "confidence": min(count / 10, 1.0)
                    })
                    
        # Find high-frequency sequences
        for seq, count in self.sequence_patterns.items():
            if count >= 5:
                action1, action2 = seq.split(' -> ')
                suggestions.append({
                    "name": f"After {action1}, do {action2}",
                    "trigger": f"state change from {action1}",
                    "action": action2,
                    "confidence": min(count / 10, 1.0)
                })
                
        return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)
        
    def get_stats(self) -> Dict[str, int]:
        """Get pattern learning stats."""
        return {
            "time_patterns": len(self.time_patterns),
            "sequence_patterns": len(self.sequence_patterns),
            "location_patterns": len(self.location_patterns)
        }
```

**Acceptance Criteria:**
- [ ] Actions logged with timestamps
- [ ] Time-based patterns detected
- [ ] Sequence patterns detected
- [ ] Predictions generated
- [ ] Automation suggestions from patterns
- [ ] Patterns persist across restarts

---

## 🧪 Validation Commands

```bash
# 1. Test vector memory
python -c "
from memory.vector_store import VectorMemory
vm = VectorMemory()
vm.add_conversation('We talked about turning on lights at bedtime', {'session': 'test'})
print(vm.search('lights bedtime'))
"

# 2. Test daily digest
python -c "
from digests.daily_digest import DailyDigestGenerator
gen = DailyDigestGenerator()
digest = gen.generate_digest()
print(digest['summary'])
"

# 3. Test pattern learner
python -c "
from patterns.behavioral_learner import BehavioralPatternLearner
bl = BehavioralPatternLearner()
for _ in range(10):
    bl.observe_action('turn_on light.living', 'light.living_room')
print(bl.suggest_automations())
"

# 4. Run all tests
pytest tests/test_advanced_features.py -v
```

---

## ✅ Definition of Done

- [ ] Vector memory stores and retrieves semantically
- [ ] Daily digests generated and sent at 7am
- [ ] Weekly reviews generated on Sundays
- [ ] Satellite discovery working
- [ ] Camera events analyzed with vision model
- [ ] Behavioral patterns learned and stored
- [ ] Automation suggestions generated from patterns
- [ ] All tests pass

---

## 📁 Files to Create

| File | Purpose |
|------|---------|
| `Smart_Home/memory/vector_store.py` | ChromaDB vector memory |
| `Smart_Home/digests/daily_digest.py` | Daily summary generator |
| `Smart_Home/digests/weekly_review.py` | Weekly review generator |
| `Smart_Home/satellites/discovery.py` | Satellite discovery |
| `Smart_Home/cameras/event_processor.py` | Camera AI analysis |
| `Smart_Home/patterns/behavioral_learner.py` | Pattern learning |
| `Smart_Home/tests/test_advanced_features.py` | Test suite |

---

## 🔗 Dependencies

**Python:**
```
chromadb>=0.4.0
sentence-transformers>=2.2.0
httpx>=0.24.0
```

**Models:**
```bash
# For camera analysis
ollama pull llava:7b
# Or
ollama pull moondream
```

**From Prior Issues:**
- Tool Broker (Issue #1)
- Session recordings (Issue #2-3)
- Secretary pipeline (Issue #4)

---

**END OF HANDOFF**
