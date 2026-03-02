"""Session archival system."""

import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..config import secretary_config

logger = logging.getLogger(__name__)


class ArchivalSystem:
    """
    Manages session archival and retention.
    
    Implements P7-06: Session Archival System.
    Creates organized archive structure and maintains session index.
    """
    
    def __init__(self, base_dir: Path = None):
        """
        Initialize archival system.
        
        Args:
            base_dir: Base directory for session archives
        """
        self.base_dir = base_dir or secretary_config.session_base_dir
        self.index_file = self.base_dir / "session_index.json"
        self.index = self._load_index()
    
    def create_session_directory(self, session_id: str = None) -> Path:
        """
        Create directory structure for new session.
        
        Args:
            session_id: Session identifier (auto-generated if not provided)
            
        Returns:
            Path to session directory
        """
        if not session_id:
            session_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        
        # Create path: /hub_sessions/YYYY/MM/DD/session_id/
        now = datetime.utcnow()
        session_dir = (
            self.base_dir
            / str(now.year)
            / f"{now.month:02d}"
            / f"{now.day:02d}"
            / session_id
        )
        
        session_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created session directory: {session_dir}")
        
        return session_dir
    
    def archive_session(
        self,
        session_dir: Path,
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Archive a completed session.
        
        Args:
            session_dir: Path to session working directory
            session_id: Session identifier
            metadata: Optional session metadata
            
        Returns:
            True if archival successful
        """
        try:
            logger.info(f"Archiving session {session_id}")
            
            # Verify required artifacts exist
            required_files = [
                secretary_config.transcript_live_file,
                secretary_config.notes_live_file,
            ]
            
            for filename in required_files:
                if not (session_dir / filename).exists():
                    logger.warning(f"Missing required file: {filename}")
            
            # Add to index
            self._add_to_index(session_id, session_dir, metadata)
            
            logger.info(f"Session {session_id} archived successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving session: {e}")
            return False
    
    def _add_to_index(
        self,
        session_id: str,
        session_dir: Path,
        metadata: Optional[Dict] = None
    ):
        """Add session to searchable index."""
        entry = {
            "session_id": session_id,
            "path": str(session_dir),
            "archived_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        
        self.index["sessions"].append(entry)
        self._save_index()
    
    def _load_index(self) -> Dict:
        """Load session index from disk."""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except Exception as e:
                logger.error(f"Error loading index: {e}")
        
        # Create new index
        return {"sessions": [], "version": "1.0"}
    
    def _save_index(self):
        """Save session index to disk."""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self.index_file.write_text(json.dumps(self.index, indent=2))
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def search_sessions(
        self,
        query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search archived sessions.
        
        Args:
            query: Text query to search in metadata
            start_date: Filter sessions after this date
            end_date: Filter sessions before this date
            limit: Maximum number of results
            
        Returns:
            List of matching session entries
        """
        results = self.index["sessions"]
        
        # Apply filters
        if start_date:
            results = [
                s for s in results
                if datetime.fromisoformat(s["archived_at"]) >= start_date
            ]
        
        if end_date:
            results = [
                s for s in results
                if datetime.fromisoformat(s["archived_at"]) <= end_date
            ]
        
        if query:
            query_lower = query.lower()
            results = [
                s for s in results
                if query_lower in json.dumps(s).lower()
            ]
        
        # Sort by date (newest first)
        results.sort(
            key=lambda s: datetime.fromisoformat(s["archived_at"]),
            reverse=True
        )
        
        return results[:limit]
    
    def apply_retention_policy(self, dry_run: bool = True) -> List[str]:
        """
        Clean up old sessions per retention policy.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            List of session IDs that were (or would be) deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(
            days=secretary_config.max_session_retention_days
        )
        
        to_delete = []
        
        for session in self.index["sessions"]:
            archived_at = datetime.fromisoformat(session["archived_at"])
            
            if archived_at < cutoff_date:
                to_delete.append(session)
        
        if not dry_run:
            for session in to_delete:
                try:
                    session_path = Path(session["path"])
                    if session_path.exists():
                        shutil.rmtree(session_path)
                        logger.info(f"Deleted old session: {session['session_id']}")
                    
                    self.index["sessions"].remove(session)
                    
                except Exception as e:
                    logger.error(f"Error deleting session {session['session_id']}: {e}")
            
            self._save_index()
        
        deleted_ids = [s["session_id"] for s in to_delete]
        
        if dry_run:
            logger.info(f"Would delete {len(deleted_ids)} old sessions (dry run)")
        else:
            logger.info(f"Deleted {len(deleted_ids)} old sessions")
        
        return deleted_ids
    
    def get_session_stats(self) -> Dict:
        """Get statistics about archived sessions."""
        total_sessions = len(self.index["sessions"])
        
        if total_sessions == 0:
            return {
                "total_sessions": 0,
                "oldest_session": None,
                "newest_session": None,
                "total_size_mb": 0,
            }
        
        dates = [
            datetime.fromisoformat(s["archived_at"])
            for s in self.index["sessions"]
        ]
        
        # Calculate total size
        total_size = 0
        for session in self.index["sessions"]:
            session_path = Path(session["path"])
            if session_path.exists():
                total_size += sum(
                    f.stat().st_size
                    for f in session_path.rglob("*")
                    if f.is_file()
                )
        
        return {
            "total_sessions": total_sessions,
            "oldest_session": min(dates).isoformat(),
            "newest_session": max(dates).isoformat(),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
