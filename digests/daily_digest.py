#!/usr/bin/env python3
"""
Daily Digest Generator.

Aggregates all sessions from the previous day and generates a summary
with key decisions, action items, and follow-ups.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional


class DailyDigestGenerator:
    """Generate daily summaries from session archives."""
    
    def __init__(
        self,
        archive_dir: str = "~/hub_memory/archives",
        digest_dir: str = "~/hub_memory/digests/daily"
    ):
        """
        Initialize digest generator.
        
        Args:
            archive_dir: Directory containing session archives
            digest_dir: Directory to save digests
        """
        self.archive_dir = Path(archive_dir).expanduser()
        self.digest_dir = Path(digest_dir).expanduser()
        self.digest_dir.mkdir(parents=True, exist_ok=True)
    
    def get_sessions_for_date(self, date: datetime) -> List[Path]:
        """
        Get all session archives for a specific date.
        
        Args:
            date: Date to fetch sessions for
            
        Returns:
            List of session archive file paths
        """
        date_str = date.strftime("%Y-%m-%d")
        sessions = []
        
        if self.archive_dir.exists():
            for session_file in self.archive_dir.glob(f"session_{date_str}_*.json"):
                sessions.append(session_file)
        
        return sorted(sessions)
    
    def load_session(self, session_path: Path) -> Optional[Dict]:
        """Load a session archive file."""
        try:
            with open(session_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session {session_path}: {e}")
            return None
    
    def extract_action_items(self, session: Dict) -> List[str]:
        """Extract action items from a session."""
        action_items = []
        
        # Look in summary if available
        if "summary" in session:
            summary = session["summary"]
            if "action_items" in summary:
                action_items.extend(summary["action_items"])
        
        # Look in transcript for explicit action language
        if "transcript" in session:
            for turn in session["transcript"]:
                text = turn.get("text", "").lower()
                if any(keyword in text for keyword in ["need to", "should", "will", "todo", "remember to"]):
                    action_items.append(turn.get("text", ""))
        
        return action_items
    
    def extract_decisions(self, session: Dict) -> List[str]:
        """Extract key decisions from a session."""
        decisions = []
        
        if "summary" in session:
            summary = session["summary"]
            if "decisions" in summary:
                decisions.extend(summary["decisions"])
        
        # Look for decision language in transcript
        if "transcript" in session:
            for turn in session["transcript"]:
                text = turn.get("text", "").lower()
                if any(keyword in text for keyword in ["decided", "agreed", "confirmed", "settled on"]):
                    decisions.append(turn.get("text", ""))
        
        return decisions
    
    def extract_automations(self, session: Dict) -> List[Dict]:
        """Extract automation commands from a session."""
        automations = []
        
        if "commands" in session:
            for cmd in session["commands"]:
                if cmd.get("type") == "automation" or "automation" in cmd.get("action", "").lower():
                    automations.append({
                        "timestamp": cmd.get("timestamp"),
                        "action": cmd.get("action"),
                        "details": cmd.get("details", {})
                    })
        
        return automations
    
    def generate_digest(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate daily digest for a specific date.
        
        Args:
            date: Date to generate digest for (defaults to yesterday)
            
        Returns:
            Digest data dictionary
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)
        
        sessions = self.get_sessions_for_date(date)
        
        # Aggregate data
        all_action_items = []
        all_decisions = []
        all_automations = []
        session_count = 0
        total_duration = 0
        
        for session_path in sessions:
            session = self.load_session(session_path)
            if session:
                session_count += 1
                total_duration += session.get("duration_seconds", 0)
                
                all_action_items.extend(self.extract_action_items(session))
                all_decisions.extend(self.extract_decisions(session))
                all_automations.extend(self.extract_automations(session))
        
        # Create digest
        digest = {
            "date": date.strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "session_count": session_count,
                "total_duration_minutes": round(total_duration / 60, 1),
                "action_items_count": len(all_action_items),
                "decisions_count": len(all_decisions),
                "automations_count": len(all_automations)
            },
            "action_items": all_action_items[:10],  # Top 10
            "decisions": all_decisions[:10],
            "automations": all_automations,
            "highlights": self._generate_highlights(session_count, all_action_items, all_decisions)
        }
        
        # Save digest
        digest_path = self.digest_dir / f"digest_{date.strftime('%Y-%m-%d')}.json"
        with open(digest_path, 'w') as f:
            json.dump(digest, f, indent=2)
        
        return digest
    
    def _generate_highlights(
        self,
        session_count: int,
        action_items: List[str],
        decisions: List[str]
    ) -> List[str]:
        """Generate human-readable highlights."""
        highlights = []
        
        if session_count > 0:
            highlights.append(f"You had {session_count} conversation{'s' if session_count > 1 else ''} with the system")
        
        if action_items:
            highlights.append(f"{len(action_items)} action item{'s' if len(action_items) > 1 else ''} identified")
        
        if decisions:
            highlights.append(f"{len(decisions)} decision{'s' if len(decisions) > 1 else ''} made")
        
        return highlights
    
    def format_digest_for_notification(self, digest: Dict) -> str:
        """
        Format digest as a human-readable notification.
        
        Args:
            digest: Digest data
            
        Returns:
            Formatted text
        """
        lines = [
            f"📅 Daily Summary for {digest['date']}",
            "",
            "Highlights:",
        ]
        
        for highlight in digest.get("highlights", []):
            lines.append(f"  • {highlight}")
        
        if digest.get("action_items"):
            lines.append("")
            lines.append("Action Items:")
            for item in digest["action_items"][:5]:
                lines.append(f"  • {item[:100]}...")
        
        if digest.get("decisions"):
            lines.append("")
            lines.append("Key Decisions:")
            for decision in digest["decisions"][:5]:
                lines.append(f"  • {decision[:100]}...")
        
        return "\n".join(lines)
    
    def get_recent_digests(self, days: int = 7) -> List[Dict]:
        """
        Get recent digests.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of digest data
        """
        digests = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i+1)
            digest_path = self.digest_dir / f"digest_{date.strftime('%Y-%m-%d')}.json"
            if digest_path.exists():
                with open(digest_path, 'r') as f:
                    digests.append(json.load(f))
        
        return digests
