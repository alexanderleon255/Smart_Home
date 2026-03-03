#!/usr/bin/env python3
"""
Behavioral Pattern Learner.

Learns user behavior patterns from historical actions to suggest automations
and predict likely next actions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter


class BehavioralPatternLearner:
    """Learn behavioral patterns from user actions."""
    
    def __init__(
        self,
        patterns_dir: str = "~/hub_memory/patterns"
    ):
        """
        Initialize pattern learner.
        
        Args:
            patterns_dir: Directory to store learned patterns
        """
        self.patterns_dir = Path(patterns_dir).expanduser()
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        
        # Pattern storage
        self.time_patterns = defaultdict(lambda: defaultdict(int))
        self.sequence_patterns = defaultdict(int)
        self.location_patterns = defaultdict(lambda: defaultdict(int))
        
        # Load existing patterns
        self._load_patterns()
    
    def _load_patterns(self):
        """Load patterns from disk."""
        patterns_file = self.patterns_dir / "learned_patterns.json"
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                data = json.load(f)
                
                # Convert back to defaultdicts
                self.time_patterns = defaultdict(
                    lambda: defaultdict(int),
                    {k: defaultdict(int, v) for k, v in data.get("time_patterns", {}).items()}
                )
                self.sequence_patterns = defaultdict(int, data.get("sequence_patterns", {}))
                self.location_patterns = defaultdict(
                    lambda: defaultdict(int),
                    {k: defaultdict(int, v) for k, v in data.get("location_patterns", {}).items()}
                )
    
    def _save_patterns(self):
        """Save patterns to disk."""
        patterns_file = self.patterns_dir / "learned_patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump({
                "time_patterns": {k: dict(v) for k, v in self.time_patterns.items()},
                "sequence_patterns": dict(self.sequence_patterns),
                "location_patterns": {k: dict(v) for k, v in self.location_patterns.items()}
            }, f, indent=2)
    
    def observe_action(
        self,
        action: str,
        entity_id: str,
        location: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Record an observed action for pattern learning.
        
        Args:
            action: Action performed (e.g., "turn_on", "turn_off")
            entity_id: Entity affected (e.g., "light.living_room")
            location: Location/room where action occurred
            timestamp: When the action occurred
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Create action signature
        action_sig = f"{action} {entity_id}"
        
        # Time-based patterns (hour of day, day of week)
        hour = timestamp.hour
        day = timestamp.strftime("%A")
        time_key = f"{day}_{hour:02d}"
        
        self.time_patterns[time_key][action_sig] += 1
        
        # Location-based patterns
        if location:
            self.location_patterns[location][action_sig] += 1
        
        # Save periodically (every 10 observations)
        total_observations = sum(sum(v.values()) for v in self.time_patterns.values())
        if total_observations % 10 == 0:
            self._save_patterns()
    
    def observe_sequence(self, actions: List[str]):
        """
        Record action sequences.
        
        Args:
            actions: List of action signatures in order
        """
        if len(actions) < 2:
            return
        
        # Record 2-grams (pairs)
        for i in range(len(actions) - 1):
            seq = f"{actions[i]} → {actions[i+1]}"
            self.sequence_patterns[seq] += 1
        
        # Record 3-grams if enough actions
        if len(actions) >= 3:
            for i in range(len(actions) - 2):
                seq = f"{actions[i]} → {actions[i+1]} → {actions[i+2]}"
                self.sequence_patterns[seq] += 1
        
        self._save_patterns()
    
    def predict_next_action(
        self,
        current_time: Optional[datetime] = None,
        location: Optional[str] = None,
        last_action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Predict likely next actions based on patterns.
        
        Args:
            current_time: Current time (defaults to now)
            location: Current location
            last_action: Last action performed
            
        Returns:
            List of predictions with confidence scores
        """
        if current_time is None:
            current_time = datetime.now()
        
        predictions = []
        
        # Time-based predictions
        hour = current_time.hour
        day = current_time.strftime("%A")
        time_key = f"{day}_{hour:02d}"
        
        if time_key in self.time_patterns:
            time_actions = self.time_patterns[time_key]
            total = sum(time_actions.values())
            
            for action, count in sorted(time_actions.items(), key=lambda x: x[1], reverse=True)[:5]:
                predictions.append({
                    "action": action,
                    "confidence": count / total,
                    "source": "time_pattern",
                    "context": f"{day} at {hour}:00"
                })
        
        # Sequence-based predictions
        if last_action:
            for seq, count in self.sequence_patterns.items():
                if seq.startswith(f"{last_action} →"):
                    next_action = seq.split(" → ")[1]
                    predictions.append({
                        "action": next_action,
                        "confidence": min(count / 10, 0.9),
                        "source": "sequence_pattern",
                        "context": f"After {last_action}"
                    })
        
        # Location-based predictions
        if location and location in self.location_patterns:
            loc_actions = self.location_patterns[location]
            total = sum(loc_actions.values())
            
            for action, count in sorted(loc_actions.items(), key=lambda x: x[1], reverse=True)[:3]:
                predictions.append({
                    "action": action,
                    "confidence": count / total * 0.7,  # Weight location lower
                    "source": "location_pattern",
                    "context": f"In {location}"
                })
        
        # Deduplicate and sort by confidence
        seen = set()
        unique_predictions = []
        for pred in sorted(predictions, key=lambda x: x["confidence"], reverse=True):
            if pred["action"] not in seen:
                seen.add(pred["action"])
                unique_predictions.append(pred)
        
        return unique_predictions[:5]
    
    def suggest_automations(
        self,
        min_occurrences: int = 5,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Suggest automations based on learned patterns.
        
        Args:
            min_occurrences: Minimum occurrences to suggest
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of automation suggestions
        """
        suggestions = []
        
        # Time-based automation suggestions
        for time_key, actions in self.time_patterns.items():
            total = sum(actions.values())
            
            for action, count in actions.items():
                if count >= min_occurrences:
                    confidence = count / total
                    if confidence >= min_confidence:
                        day, hour = time_key.split('_')
                        suggestions.append({
                            "type": "time_based",
                            "name": f"Auto-{action} at {hour}:00 on {day}s",
                            "trigger": {
                                "platform": "time",
                                "at": f"{hour}:00:00"
                            },
                            "condition": {
                                "condition": "time",
                                "weekday": day.lower()
                            },
                            "action": action,
                            "confidence": confidence,
                            "occurrences": count
                        })
        
        # Sequence-based automation suggestions
        for seq, count in self.sequence_patterns.items():
            if count >= min_occurrences:
                parts = seq.split(" → ")
                if len(parts) == 2:
                    trigger_action, next_action = parts
                    confidence = min(count / 10, 1.0)
                    
                    if confidence >= min_confidence:
                        suggestions.append({
                            "type": "sequence_based",
                            "name": f"After '{trigger_action}', do '{next_action}'",
                            "trigger": {
                                "platform": "state",
                                "trigger_action": trigger_action
                            },
                            "action": next_action,
                            "confidence": confidence,
                            "occurrences": count
                        })
        
        # Sort by confidence
        return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)
    
    def detect_anomalies(
        self,
        recent_actions: List[Dict[str, Any]],
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous behavior (actions that deviate from patterns).
        
        Args:
            recent_actions: List of recent actions with timestamps
            threshold: Confidence threshold for "normal" behavior
            
        Returns:
            List of anomalous actions
        """
        anomalies = []
        
        for action_data in recent_actions:
            action = action_data.get("action")
            timestamp = action_data.get("timestamp")
            location = action_data.get("location")
            
            if not action or not timestamp:
                continue
            
            # Get predictions for this context
            predictions = self.predict_next_action(
                current_time=timestamp,
                location=location
            )
            
            # Check if action is in predictions
            predicted_actions = [p["action"] for p in predictions if p["confidence"] > threshold]
            
            if action not in predicted_actions and predictions:
                anomalies.append({
                    "action": action,
                    "timestamp": timestamp,
                    "expected": predicted_actions[:3] if predicted_actions else ["(no pattern)"],
                    "deviation_score": 1.0 - max([p["confidence"] for p in predictions if p["action"] == action], default=0.0)
                })
        
        return anomalies
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get pattern learning statistics.
        
        Returns:
            Statistics dictionary
        """
        total_time_observations = sum(sum(v.values()) for v in self.time_patterns.values())
        total_sequences = sum(self.sequence_patterns.values())
        total_location_observations = sum(sum(v.values()) for v in self.location_patterns.values())
        
        # Find most common patterns
        all_actions = Counter()
        for actions in self.time_patterns.values():
            all_actions.update(actions)
        
        return {
            "total_observations": total_time_observations,
            "time_patterns_count": len(self.time_patterns),
            "sequence_patterns_count": len(self.sequence_patterns),
            "location_patterns_count": len(self.location_patterns),
            "total_sequences_observed": total_sequences,
            "total_location_observations": total_location_observations,
            "most_common_actions": all_actions.most_common(5)
        }
    
    def export_patterns(self, output_file: str):
        """
        Export patterns to a human-readable format.
        
        Args:
            output_file: Path to output file
        """
        output_path = Path(output_file).expanduser()
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "stats": self.get_stats(),
            "time_patterns": {k: dict(v) for k, v in self.time_patterns.items()},
            "sequence_patterns": dict(self.sequence_patterns),
            "location_patterns": {k: dict(v) for k, v in self.location_patterns.items()},
            "automation_suggestions": self.suggest_automations()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
