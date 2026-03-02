"""Secretary engine for live note extraction."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

from ..config import secretary_config
from ..prompts import (
    LIVE_SECRETARY_SYSTEM_PROMPT,
    FINAL_NOTES_SYSTEM_PROMPT,
    MEMORY_EXTRACTION_SYSTEM_PROMPT,
    AUTOMATION_HOOK_SYSTEM_PROMPT,
)
from ..schemas import LiveNotes, MemoryUpdate, ActionItem

logger = logging.getLogger(__name__)


class SecretaryEngine:
    """
    Live secretary engine using Llama for structured note extraction.
    
    Implements P7-02: Live Secretary Engine
    Processes rolling transcript and generates structured notes.
    """
    
    def __init__(
        self,
        ollama_url: str = None,
        model: str = None,
        update_interval: int = None,
        session_dir: Path = None,
    ):
        """
        Initialize secretary engine.
        
        Args:
            ollama_url: Ollama API URL
            model: LLM model to use
            update_interval: Seconds between live note updates
            session_dir: Directory to write notes files
        """
        self.ollama_url = ollama_url or secretary_config.ollama_url
        self.model = model or secretary_config.ollama_model
        self.update_interval = update_interval or secretary_config.secretary_update_interval_seconds
        self.session_dir = session_dir or Path.cwd()
        
        self.notes_live_file = self.session_dir / secretary_config.notes_live_file
        self.notes_final_file = self.session_dir / secretary_config.notes_final_file
        self.memory_update_file = self.session_dir / secretary_config.memory_update_file
        
        self.current_notes = LiveNotes()
        self.is_running = False
    
    async def start_live_processing(self, get_transcript_func):
        """
        Start live note processing loop.
        
        Args:
            get_transcript_func: Function that returns current transcript window
        """
        self.is_running = True
        logger.info("Starting live secretary processing")
        
        try:
            while self.is_running:
                await asyncio.sleep(self.update_interval)
                
                # Get rolling transcript window
                transcript = get_transcript_func()
                
                if not transcript or transcript.strip() == "":
                    continue
                
                # Process transcript and update notes
                await self._update_live_notes(transcript)
                
        except Exception as e:
            logger.error(f"Live processing error: {e}")
            raise
        finally:
            self.is_running = False
    
    async def _update_live_notes(self, transcript: str):
        """Process transcript and update live notes."""
        try:
            # Call LLM to extract structured information
            prompt = f"Analyze this conversation transcript and extract structured notes:\n\n{transcript}"
            
            response = await self._call_llm(LIVE_SECRETARY_SYSTEM_PROMPT, prompt)
            
            # Parse JSON response
            data = json.loads(response)
            
            # Update live notes
            self.current_notes.last_updated = datetime.utcnow()
            self.current_notes.rolling_summary = data.get("rolling_summary", "")
            self.current_notes.decisions = data.get("decisions", [])
            
            # Parse action items
            action_items = []
            for item_data in data.get("action_items", []):
                item = ActionItem(
                    task=item_data.get("task", ""),
                    owner=item_data.get("owner"),
                    due_date=item_data.get("due_date"),
                )
                action_items.append(item)
            self.current_notes.action_items = action_items
            
            self.current_notes.open_questions = data.get("open_questions", [])
            self.current_notes.memory_candidates = data.get("memory_candidates", [])
            self.current_notes.automation_opportunities = data.get("automation_opportunities", [])
            
            # Write to file
            self.notes_live_file.write_text(self.current_notes.to_markdown())
            
            logger.info("Updated live notes")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        except Exception as e:
            logger.error(f"Error updating live notes: {e}")
    
    async def generate_final_notes(self, final_transcript: str) -> str:
        """
        Generate final comprehensive notes from complete transcript.
        
        Implements P7-04: Final Notes Generation.
        
        Args:
            final_transcript: Complete high-accuracy transcript
            
        Returns:
            Final notes markdown
        """
        logger.info("Generating final notes")
        
        prompt = f"Create comprehensive final notes from this complete conversation:\n\n{final_transcript}"
        
        try:
            notes_md = await self._call_llm(FINAL_NOTES_SYSTEM_PROMPT, prompt)
            
            # Write to file
            self.notes_final_file.write_text(notes_md)
            
            logger.info(f"Wrote final notes to {self.notes_final_file}")
            return notes_md
            
        except Exception as e:
            logger.error(f"Error generating final notes: {e}")
            raise
    
    async def generate_memory_update(
        self,
        final_transcript: str,
        session_id: str
    ) -> MemoryUpdate:
        """
        Generate structured memory update from conversation.
        
        Implements P7-05: Memory Update Generation.
        
        Args:
            final_transcript: Complete conversation transcript
            session_id: Session identifier
            
        Returns:
            MemoryUpdate object
        """
        logger.info("Generating memory update")
        
        prompt = f"Extract memory-worthy information from this conversation:\n\n{final_transcript}"
        
        try:
            response = await self._call_llm(MEMORY_EXTRACTION_SYSTEM_PROMPT, prompt)
            data = json.loads(response)
            
            # Create memory update
            memory_update = MemoryUpdate(
                session_id=session_id,
                extractions=data.get("extractions", [])
            )
            
            # Write to file
            self.memory_update_file.write_text(memory_update.model_dump_json(indent=2))
            
            logger.info(f"Wrote memory update to {self.memory_update_file}")
            return memory_update
            
        except Exception as e:
            logger.error(f"Error generating memory update: {e}")
            raise
    
    async def detect_automation_hooks(self, transcript: str) -> dict:
        """
        Detect automation opportunities in transcript.
        
        Implements P7-07: Automation Hook Detection.
        
        Args:
            transcript: Conversation transcript
            
        Returns:
            Dict of detected automation opportunities
        """
        logger.info("Detecting automation hooks")
        
        prompt = f"Detect automation opportunities in this conversation:\n\n{transcript}"
        
        try:
            response = await self._call_llm(AUTOMATION_HOOK_SYSTEM_PROMPT, prompt)
            data = json.loads(response)
            
            logger.info(f"Detected {len(data.get('opportunities', []))} automation opportunities")
            return data
            
        except Exception as e:
            logger.error(f"Error detecting automation hooks: {e}")
            raise
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make API call to Ollama."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3},
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=120.0
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
    
    def stop(self):
        """Stop live processing."""
        logger.info("Stopping secretary engine")
        self.is_running = False
