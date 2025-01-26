import sys
import os
import logging
from pathlib import Path
import pytest
import asyncio
from datetime import datetime, timedelta
import json

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from queue_manager import QueueManager
from redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
async def clear_test_data():
    """Clear all test queue data from Redis before and after each test"""
    r = redis_client.client
    try:
        # Reset Redis state before test
        keys_to_delete = r.keys("*queue*") + r.keys("*topic*") + r.keys("*last_processed*")
        if keys_to_delete:
            r.delete(*keys_to_delete)
        yield
    finally:
        # Reset Redis state after test
        keys_to_delete = r.keys("*queue*") + r.keys("*topic*") + r.keys("*last_processed*")
        if keys_to_delete:
            r.delete(*keys_to_delete)
        # Verify Redis is empty
        remaining_keys = r.keys("*queue*") + r.keys("*topic*") + r.keys("*last_processed*")
        assert len(remaining_keys) == 0, f"Redis not properly cleared: {remaining_keys}"

@pytest.mark.asyncio
async def test_queue_operations():
    """Test basic queue operations"""
    queue_manager = QueueManager()
    
    # Test enqueueing first discussion (should be immediate)
    success, message = await queue_manager.enqueue_discussion(
        "topic1",
        "discussion1",
        "Test question 1"
    )
    assert success is True
    assert "Discussion queued" in message
    assert "wait time: 0" in message.lower(), "First discussion should have no wait time"
    
    # Test enqueueing second discussion (should be queued)
    success, message = await queue_manager.enqueue_discussion(
        "topic1",
        "discussion2",
        "Test question 2"
    )
    assert success is True
    assert "Estimated wait time" in message
    assert int(message.split(": ")[1].split(" ")[0]) >= 60, "Second discussion should wait at least 60 seconds"
    
    # Test getting queue status
    position, wait_time = await queue_manager.get_queue_status("topic1")
    assert position == 2, "Second discussion should be in position 2"
    assert wait_time >= 60, "Wait time should be at least 60 seconds"
    
    # Test getting next discussion (should get first one)
    entry = await queue_manager.get_next_discussion()
    assert entry is not None
    assert entry["topic_id"] == "topic1"
    assert entry["discussion_id"] == "discussion1"
    
    # Test immediate retry of next discussion (should be None due to rate limiting)
    entry = await queue_manager.get_next_discussion()
    assert entry is None, "Should not get second discussion before interval passes"

@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting functionality"""
    queue_manager = QueueManager()
    
    # Enqueue multiple discussions for the same topic
    discussions = []
    for i in range(3):
        success, message = await queue_manager.enqueue_discussion(
            "topic1",
            f"discussion{i}",
            f"Test question {i}"
        )
        assert success is True
        discussions.append((success, message))
    
    # Verify wait times increase by processing interval
    for i, (success, message) in enumerate(discussions):
        wait_time = int(message.split(": ")[1].split(" ")[0])
        expected_wait = max(0, i * queue_manager.processing_interval)
        assert wait_time >= expected_wait, f"Discussion {i} wait time {wait_time} should be >= {expected_wait}"
    
    # Test processing sequence
    # First discussion should be available immediately
    entry = await queue_manager.get_next_discussion()
    assert entry is not None
    assert entry["discussion_id"] == "discussion0"
    
    # Second discussion should not be available yet
    entry = await queue_manager.get_next_discussion()
    assert entry is None, "Rate limiting should prevent immediate processing of second discussion"
    
    # Different topic should be processed immediately
    success, message = await queue_manager.enqueue_discussion(
        "topic2",
        "other_discussion",
        "Test question for different topic"
    )
    assert success is True
    assert "wait time: 0" in message.lower(), "Different topic should have no wait time"
    
    entry = await queue_manager.get_next_discussion()
    assert entry is not None
    assert entry["topic_id"] == "topic2", "Different topic should be processed immediately"
