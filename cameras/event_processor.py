#!/usr/bin/env python3
"""
Camera Event Processor with AI Inference.

Processes camera events using vision models (Ollama LLaVA or Moondream)
for intelligent object detection and scene understanding.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import httpx
import base64


class CameraEventProcessor:
    """Process camera events with AI-powered analysis."""
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "llava:7b",  # or "moondream"
        event_log_dir: str = "~/hub_memory/camera_events"
    ):
        """
        Initialize camera event processor.
        
        Args:
            ollama_url: Ollama API endpoint
            model: Vision model to use
            event_log_dir: Directory to log events
        """
        self.ollama_url = ollama_url
        self.model = model
        self.event_log_dir = Path(event_log_dir).expanduser()
        self.event_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Detection categories
        self.categories = {
            "person": ["person", "people", "human", "individual"],
            "vehicle": ["car", "truck", "vehicle", "automobile"],
            "package": ["package", "box", "delivery", "parcel"],
            "animal": ["dog", "cat", "animal", "pet"],
            "unknown": []
        }
    
    async def analyze_image(
        self,
        image_path: str,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image using the vision model.
        
        Args:
            image_path: Path to image file
            prompt: Optional custom prompt
            
        Returns:
            Analysis results
        """
        # Default prompt for security camera analysis
        if prompt is None:
            prompt = (
                "Analyze this security camera image. "
                "Describe what you see, focusing on: "
                "1) Any people, vehicles, or animals "
                "2) Notable objects or packages "
                "3) Time of day indicators "
                "4) Any suspicious or unusual activity. "
                "Be specific and concise."
            )
        
        # Load and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "images": [image_data],
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "description": result.get("response", ""),
                    "model": self.model,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return {
                "description": f"Error: {str(e)}",
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "error": True
            }
    
    def categorize_event(self, description: str) -> str:
        """
        Categorize event based on description.
        
        Args:
            description: Event description from vision model
            
        Returns:
            Category name
        """
        description_lower = description.lower()
        
        for category, keywords in self.categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return "unknown"
    
    def assess_priority(self, description: str, category: str) -> str:
        """
        Assess event priority.
        
        Args:
            description: Event description
            category: Event category
            
        Returns:
            Priority level (high, medium, low)
        """
        description_lower = description.lower()
        
        # High priority indicators
        high_priority_keywords = [
            "person at door", "suspicious", "breaking", "fallen",
            "emergency", "smoke", "fire", "intruder"
        ]
        
        if any(keyword in description_lower for keyword in high_priority_keywords):
            return "high"
        
        # Medium priority
        if category in ["person", "vehicle"]:
            return "medium"
        
        # Package delivery
        if category == "package":
            return "medium"
        
        return "low"
    
    async def process_event(
        self,
        camera_id: str,
        image_path: str,
        motion_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a camera event.
        
        Args:
            camera_id: Camera identifier
            image_path: Path to captured image
            motion_metadata: Optional motion detection metadata
            
        Returns:
            Processed event data
        """
        # Analyze image
        analysis = await self.analyze_image(image_path)
        
        # Categorize and prioritize
        category = self.categorize_event(analysis["description"])
        priority = self.assess_priority(analysis["description"], category)
        
        # Create event record
        event = {
            "event_id": f"cam_{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "analysis": analysis,
            "category": category,
            "priority": priority,
            "motion_metadata": motion_metadata or {}
        }
        
        # Log event
        self._log_event(event)
        
        return event
    
    def _log_event(self, event: Dict):
        """Log event to disk."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.event_log_dir / f"events_{date_str}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def get_events(
        self,
        date: Optional[datetime] = None,
        camera_id: Optional[str] = None,
        category: Optional[str] = None,
        min_priority: str = "low"
    ) -> List[Dict]:
        """
        Retrieve logged events with filters.
        
        Args:
            date: Filter by date
            camera_id: Filter by camera
            category: Filter by category
            min_priority: Minimum priority level
            
        Returns:
            List of matching events
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        log_file = self.event_log_dir / f"events_{date_str}.jsonl"
        
        if not log_file.exists():
            return []
        
        priority_levels = {"high": 3, "medium": 2, "low": 1}
        min_level = priority_levels.get(min_priority, 1)
        
        events = []
        with open(log_file, 'r') as f:
            for line in f:
                event = json.loads(line)
                
                # Apply filters
                if camera_id and event.get("camera_id") != camera_id:
                    continue
                
                if category and event.get("category") != category:
                    continue
                
                event_priority = event.get("priority", "low")
                if priority_levels.get(event_priority, 1) < min_level:
                    continue
                
                events.append(event)
        
        return events
    
    def get_event_stats(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get event statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Statistics dictionary
        """
        from collections import Counter
        from datetime import timedelta
        
        all_events = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            all_events.extend(self.get_events(date=date))
        
        if not all_events:
            return {
                "total_events": 0,
                "categories": {},
                "priorities": {},
                "cameras": {}
            }
        
        category_counts = Counter(e.get("category") for e in all_events)
        priority_counts = Counter(e.get("priority") for e in all_events)
        camera_counts = Counter(e.get("camera_id") for e in all_events)
        
        return {
            "total_events": len(all_events),
            "categories": dict(category_counts),
            "priorities": dict(priority_counts),
            "cameras": dict(camera_counts),
            "date_range": f"{days} days"
        }
    
    async def generate_alert(
        self,
        event: Dict,
        notification_service: Optional[Any] = None
    ) -> bool:
        """
        Generate an alert for high-priority events.
        
        Args:
            event: Event data
            notification_service: Optional notification service
            
        Returns:
            True if alert sent
        """
        if event.get("priority") != "high":
            return False
        
        alert_text = (
            f"🚨 Camera Alert: {event.get('camera_id')}\n"
            f"Category: {event.get('category')}\n"
            f"Description: {event.get('analysis', {}).get('description', 'N/A')}\n"
            f"Time: {event.get('timestamp')}"
        )
        
        if notification_service:
            try:
                await notification_service.send(alert_text)
                return True
            except Exception as e:
                print(f"Error sending alert: {e}")
                return False
        else:
            print(alert_text)
            return True
