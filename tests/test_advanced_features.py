#!/usr/bin/env python3
"""
Test suite for advanced features (Issue #5).

Tests: Vector Memory, Daily/Weekly Digests, Satellite Discovery,
Camera Processing, and Behavioral Pattern Learning.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

# Import modules to test
from memory.vector_store import VectorMemory
from digests.daily_digest import DailyDigestGenerator
from digests.weekly_review import WeeklyReviewGenerator
from satellites.discovery import SatelliteDiscovery
from cameras.event_processor import CameraEventProcessor
from patterns.behavioral_learner import BehavioralPatternLearner


class TestVectorMemory:
    """Tests for P8-01: Vector Memory."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def vector_memory(self, temp_dir):
        """Create VectorMemory instance with temp directory."""
        return VectorMemory(persist_dir=temp_dir)
    
    def test_initialization(self, vector_memory):
        """Test vector memory initialization."""
        assert vector_memory is not None
        stats = vector_memory.get_stats()
        assert stats["conversations"] == 0
        assert stats["entities"] == 0
        assert stats["automations"] == 0
    
    def test_add_conversation(self, vector_memory):
        """Test adding conversations."""
        vector_memory.add_conversation(
            text="Turn on the living room lights at bedtime",
            metadata={"speaker": "user", "intent": "automation"},
            session_id="test_session_001"
        )
        
        stats = vector_memory.get_stats()
        assert stats["conversations"] == 1
    
    def test_add_entity(self, vector_memory):
        """Test adding entities."""
        vector_memory.add_entity(
            entity_type="person",
            entity_value="John",
            context="Mentioned during morning routine discussion",
            source_session="test_session_001"
        )
        
        stats = vector_memory.get_stats()
        assert stats["entities"] == 1
    
    def test_add_automation(self, vector_memory):
        """Test adding automations."""
        vector_memory.add_automation(
            name="Bedtime Routine",
            description="Turn off all lights at 11 PM",
            rationale="User wants automatic lights off for better sleep",
            config={"time": "23:00", "action": "lights.off"}
        )
        
        stats = vector_memory.get_stats()
        assert stats["automations"] == 1
    
    def test_search(self, vector_memory):
        """Test semantic search."""
        # Add some data
        vector_memory.add_conversation(
            text="Turn on the living room lights at bedtime",
            metadata={"speaker": "user"},
            session_id="test_001"
        )
        vector_memory.add_conversation(
            text="Set the thermostat to 72 degrees",
            metadata={"speaker": "user"},
            session_id="test_002"
        )
        
        # Search
        results = vector_memory.search("lights bedtime", n_results=2)
        assert len(results) > 0
        assert "bedtime" in results[0]["document"].lower() or "light" in results[0]["document"].lower()


class TestDailyDigest:
    """Tests for P8-02: Daily Digest."""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def digest_generator(self, temp_dir):
        archive_dir = Path(temp_dir) / "archives"
        digest_dir = Path(temp_dir) / "digests"
        archive_dir.mkdir()
        return DailyDigestGenerator(
            archive_dir=str(archive_dir),
            digest_dir=str(digest_dir)
        )
    
    def test_initialization(self, digest_generator):
        """Test digest generator initialization."""
        assert digest_generator is not None
        assert digest_generator.digest_dir.exists()
    
    def test_generate_empty_digest(self, digest_generator):
        """Test generating digest with no data."""
        digest = digest_generator.generate_digest()
        assert digest["summary"]["session_count"] == 0
    
    def test_format_digest(self, digest_generator):
        """Test formatting digest for notification."""
        digest = {
            "date": "2026-03-01",
            "highlights": ["You had 3 conversations", "5 action items identified"],
            "action_items": ["Buy groceries", "Call dentist"],
            "decisions": ["Agreed to weekly planning"]
        }
        
        formatted = digest_generator.format_digest_for_notification(digest)
        assert "Daily Summary" in formatted
        assert "3 conversations" in formatted


class TestWeeklyReview:
    """Tests for P8-03: Weekly Review."""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def review_generator(self, temp_dir):
        digest_dir = Path(temp_dir) / "digests"
        review_dir = Path(temp_dir) / "reviews"
        digest_dir.mkdir()
        return WeeklyReviewGenerator(
            digest_dir=str(digest_dir),
            review_dir=str(review_dir)
        )
    
    def test_initialization(self, review_generator):
        """Test review generator initialization."""
        assert review_generator is not None
        assert review_generator.review_dir.exists()
    
    def test_week_range(self, review_generator):
        """Test week range calculation."""
        test_date = datetime(2026, 3, 5)  # A Thursday
        start, end = review_generator.get_week_range(test_date)
        assert start.weekday() == 0  # Monday
        assert (end - start).days == 6


class TestSatelliteDiscovery:
    """Tests for P8-04: Voice Satellites."""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def satellite_discovery(self, temp_dir):
        return SatelliteDiscovery(config_dir=temp_dir)
    
    def test_initialization(self, satellite_discovery):
        """Test satellite discovery initialization."""
        assert satellite_discovery is not None
        assert satellite_discovery.config_dir.exists()
    
    def test_assign_room(self, satellite_discovery):
        """Test assigning room to satellite."""
        # Add a fake satellite
        satellite_discovery.satellites["sat_001"] = {
            "id": "sat_001",
            "name": "Living Room Satellite",
            "ip": "192.168.1.100"
        }
        
        # Assign room
        satellite_discovery.assign_room("sat_001", "living_room")
        assert satellite_discovery.satellites["sat_001"]["room"] == "living_room"
    
    def test_get_satellite_by_room(self, satellite_discovery):
        """Test finding satellite by room."""
        satellite_discovery.satellites["sat_002"] = {
            "id": "sat_002",
            "room": "bedroom"
        }
        
        result = satellite_discovery.get_satellite_by_room("bedroom")
        assert result == "sat_002"


class TestCameraEventProcessor:
    """Tests for P8-05: Camera AI."""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def camera_processor(self, temp_dir):
        return CameraEventProcessor(event_log_dir=temp_dir)
    
    def test_initialization(self, camera_processor):
        """Test camera processor initialization."""
        assert camera_processor is not None
        assert camera_processor.event_log_dir.exists()
    
    def test_categorize_event(self, camera_processor):
        """Test event categorization."""
        category = camera_processor.categorize_event(
            "A person is standing at the front door"
        )
        assert category == "person"
        
        category = camera_processor.categorize_event(
            "A car is parked in the driveway"
        )
        assert category == "vehicle"
    
    def test_assess_priority(self, camera_processor):
        """Test priority assessment."""
        priority = camera_processor.assess_priority(
            "Person at door ringing doorbell",
            "person"
        )
        assert priority == "high"
        
        priority = camera_processor.assess_priority(
            "A cat is walking across the yard",
            "animal"
        )
        assert priority == "low"


class TestBehavioralPatternLearner:
    """Tests for P8-06: Behavioral Patterns."""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def pattern_learner(self, temp_dir):
        return BehavioralPatternLearner(patterns_dir=temp_dir)
    
    def test_initialization(self, pattern_learner):
        """Test pattern learner initialization."""
        assert pattern_learner is not None
        assert pattern_learner.patterns_dir.exists()
    
    def test_observe_action(self, pattern_learner):
        """Test observing actions."""
        # Observe same action multiple times
        for _ in range(10):
            pattern_learner.observe_action(
                action="turn_on",
                entity_id="light.living_room",
                timestamp=datetime(2026, 3, 1, 20, 0)  # 8 PM on Saturday
            )
        
        stats = pattern_learner.get_stats()
        assert stats["total_observations"] == 10
    
    def test_observe_sequence(self, pattern_learner):
        """Test observing action sequences."""
        pattern_learner.observe_sequence([
            "turn_off light.living_room",
            "turn_on light.bedroom",
            "lock door.front"
        ])
        
        stats = pattern_learner.get_stats()
        assert stats["sequence_patterns_count"] > 0
    
    def test_suggest_automations(self, pattern_learner):
        """Test automation suggestions."""
        # Create a strong pattern
        for _ in range(10):
            pattern_learner.observe_action(
                action="turn_on",
                entity_id="light.living_room",
                timestamp=datetime(2026, 3, 1, 20, 0)
            )
        
        suggestions = pattern_learner.suggest_automations(min_occurrences=5)
        assert len(suggestions) > 0
        assert suggestions[0]["confidence"] > 0.5
    
    def test_predict_next_action(self, pattern_learner):
        """Test action prediction."""
        # Build pattern
        for _ in range(5):
            pattern_learner.observe_action(
                action="turn_on",
                entity_id="light.bedroom",
                location="bedroom",
                timestamp=datetime(2026, 3, 1, 22, 0)  # 10 PM
            )
        
        # Predict
        predictions = pattern_learner.predict_next_action(
            current_time=datetime(2026, 3, 2, 22, 0),
            location="bedroom"
        )
        
        # Should have at least one prediction
        assert len(predictions) > 0


# Integration tests
class TestIntegration:
    """Integration tests across modules."""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    def test_memory_and_digest_integration(self, temp_dir):
        """Test vector memory with digest generation."""
        # Create instances
        vm = VectorMemory(persist_dir=temp_dir + "/vector")
        
        # Add conversation data
        vm.add_conversation(
            text="Turn on lights at sunset",
            metadata={"date": "2026-03-01"},
            session_id="session_001"
        )
        
        # Search should work
        results = vm.search("sunset lights")
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
