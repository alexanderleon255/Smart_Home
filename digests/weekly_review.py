#!/usr/bin/env python3
"""
Weekly Review Generator.

Aggregates daily digests into a weekly operational review showing
patterns, trends, and action item completion tracking.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter


class WeeklyReviewGenerator:
    """Generate weekly reviews from daily digests."""
    
    def __init__(
        self,
        digest_dir: str = "~/hub_memory/digests/daily",
        review_dir: str = "~/hub_memory/digests/weekly"
    ):
        """
        Initialize weekly review generator.
        
        Args:
            digest_dir: Directory containing daily digests
            review_dir: Directory to save weekly reviews
        """
        self.digest_dir = Path(digest_dir).expanduser()
        self.review_dir = Path(review_dir).expanduser()
        self.review_dir.mkdir(parents=True, exist_ok=True)
    
    def get_week_range(self, date: Optional[datetime] = None) -> tuple:
        """
        Get start and end dates for the week containing the given date.
        
        Args:
            date: Reference date (defaults to today)
            
        Returns:
            Tuple of (start_date, end_date)
        """
        if date is None:
            date = datetime.now()
        
        # Find Monday of the week
        start = date - timedelta(days=date.weekday())
        end = start + timedelta(days=6)
        
        return (start, end)
    
    def load_daily_digests(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Load all daily digests in a date range.
        
        Args:
            start_date: Start of range
            end_date: End of range
            
        Returns:
            List of digest data
        """
        digests = []
        current = start_date
        
        while current <= end_date:
            digest_path = self.digest_dir / f"digest_{current.strftime('%Y-%m-%d')}.json"
            if digest_path.exists():
                with open(digest_path, 'r') as f:
                    digests.append(json.load(f))
            current += timedelta(days=1)
        
        return digests
    
    def analyze_patterns(self, digests: List[Dict]) -> Dict[str, Any]:
        """
        Analyze patterns across daily digests.
        
        Args:
            digests: List of daily digests
            
        Returns:
            Pattern analysis data
        """
        # Activity patterns
        sessions_by_day = {}
        total_sessions = 0
        total_duration = 0
        
        for digest in digests:
            day = digest.get("date")
            summary = digest.get("summary", {})
            
            sessions_by_day[day] = summary.get("session_count", 0)
            total_sessions += summary.get("session_count", 0)
            total_duration += summary.get("total_duration_minutes", 0)
        
        # Most active day
        most_active_day = max(sessions_by_day.items(), key=lambda x: x[1]) if sessions_by_day else (None, 0)
        
        # Action item trends
        action_items_trend = []
        for digest in digests:
            action_items_trend.append({
                "date": digest.get("date"),
                "count": digest.get("summary", {}).get("action_items_count", 0)
            })
        
        return {
            "total_sessions": total_sessions,
            "total_duration_minutes": round(total_duration, 1),
            "avg_sessions_per_day": round(total_sessions / len(digests), 1) if digests else 0,
            "most_active_day": most_active_day[0] if most_active_day[0] else "N/A",
            "most_active_day_sessions": most_active_day[1],
            "action_items_trend": action_items_trend
        }
    
    def track_action_items(self, digests: List[Dict]) -> Dict[str, Any]:
        """
        Track action items mentioned across the week.
        
        Args:
            digests: List of daily digests
            
        Returns:
            Action item tracking data
        """
        all_items = []
        
        for digest in digests:
            items = digest.get("action_items", [])
            date = digest.get("date")
            for item in items:
                all_items.append({
                    "date": date,
                    "item": item
                })
        
        # Detect recurring themes (simple keyword frequency)
        all_text = " ".join([item["item"].lower() for item in all_items])
        words = all_text.split()
        common_words = Counter(words).most_common(10)
        
        return {
            "total_items": len(all_items),
            "items_by_day": {
                digest["date"]: len(digest.get("action_items", []))
                for digest in digests
            },
            "recurring_themes": [word for word, count in common_words if len(word) > 4]
        }
    
    def identify_trends(self, digests: List[Dict]) -> List[str]:
        """
        Identify notable trends in the week's data.
        
        Args:
            digests: List of daily digests
            
        Returns:
            List of trend descriptions
        """
        trends = []
        
        if not digests:
            return ["No data available for trend analysis"]
        
        # Session frequency trend
        session_counts = [d.get("summary", {}).get("session_count", 0) for d in digests]
        if len(session_counts) >= 2:
            if session_counts[-1] > session_counts[0]:
                trends.append("📈 Increasing session frequency")
            elif session_counts[-1] < session_counts[0]:
                trends.append("📉 Decreasing session frequency")
        
        # Action item trend
        action_counts = [d.get("summary", {}).get("action_items_count", 0) for d in digests]
        avg_actions = sum(action_counts) / len(action_counts) if action_counts else 0
        if avg_actions > 5:
            trends.append("⚡ High action item generation (avg {:.1f}/day)".format(avg_actions))
        
        # Automation activity
        automation_counts = [d.get("summary", {}).get("automations_count", 0) for d in digests]
        total_automations = sum(automation_counts)
        if total_automations > 0:
            trends.append(f"🤖 {total_automations} automation{'s' if total_automations > 1 else ''} created")
        
        return trends if trends else ["Steady operational week"]
    
    def generate_review(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate weekly review.
        
        Args:
            date: Reference date (defaults to current week)
            
        Returns:
            Weekly review data
        """
        start_date, end_date = self.get_week_range(date)
        digests = self.load_daily_digests(start_date, end_date)
        
        # Generate review
        review = {
            "week_start": start_date.strftime("%Y-%m-%d"),
            "week_end": end_date.strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "patterns": self.analyze_patterns(digests),
            "action_items": self.track_action_items(digests),
            "trends": self.identify_trends(digests),
            "daily_summaries": [
                {
                    "date": d.get("date"),
                    "sessions": d.get("summary", {}).get("session_count", 0),
                    "highlights": d.get("highlights", [])
                }
                for d in digests
            ]
        }
        
        # Save review
        review_path = self.review_dir / f"review_{start_date.strftime('%Y-W%W')}.json"
        with open(review_path, 'w') as f:
            json.dump(review, f, indent=2)
        
        return review
    
    def format_review_for_notification(self, review: Dict) -> str:
        """
        Format review as human-readable notification.
        
        Args:
            review: Review data
            
        Returns:
            Formatted text
        """
        lines = [
            f"📊 Weekly Review: {review['week_start']} to {review['week_end']}",
            "",
            "Overview:",
        ]
        
        patterns = review.get("patterns", {})
        lines.append(f"  • {patterns.get('total_sessions', 0)} total sessions")
        lines.append(f"  • {patterns.get('total_duration_minutes', 0)} minutes total")
        lines.append(f"  • Most active: {patterns.get('most_active_day', 'N/A')}")
        
        lines.append("")
        lines.append("Trends:")
        for trend in review.get("trends", []):
            lines.append(f"  • {trend}")
        
        action_items = review.get("action_items", {})
        if action_items.get("total_items", 0) > 0:
            lines.append("")
            lines.append(f"Action Items: {action_items['total_items']} tracked")
            if action_items.get("recurring_themes"):
                lines.append(f"  Recurring themes: {', '.join(action_items['recurring_themes'][:5])}")
        
        return "\n".join(lines)
    
    def get_recent_reviews(self, weeks: int = 4) -> List[Dict]:
        """
        Get recent weekly reviews.
        
        Args:
            weeks: Number of weeks to look back
            
        Returns:
            List of review data
        """
        reviews = []
        current_date = datetime.now()
        
        for i in range(weeks):
            date = current_date - timedelta(weeks=i)
            start_date, _ = self.get_week_range(date)
            review_path = self.review_dir / f"review_{start_date.strftime('%Y-W%W')}.json"
            
            if review_path.exists():
                with open(review_path, 'r') as f:
                    reviews.append(json.load(f))
        
        return reviews
