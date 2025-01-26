import sys
import os
import logging
from pathlib import Path
import pytest
from datetime import datetime, timedelta
import json

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import create_discussion, update_discussion, get_discussions
from redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
async def clear_test_data():
    """Clear all test data from Redis before and after each test"""
    r = redis_client.client
    try:
        keys_to_delete = r.keys("test_*")
        if keys_to_delete:
            r.delete(*keys_to_delete)
        yield
    finally:
        keys_to_delete = r.keys("test_*")
        if keys_to_delete:
            r.delete(*keys_to_delete)

def test_discussion_timing_storage():
    """Test storing and retrieving discussion timing information"""
    topic_id = "test_topic_1"
    question = "Test question"
    
    # Create mock responses with timing information
    now = datetime.now()
    responses = [
        {
            "agent_id": "agent1",
            "framework": "rig",
            "response": "Response 1",
            "processing_start": now,
            "processing_end": now + timedelta(seconds=1),
            "total_time_seconds": 1.0,
            "votes": 0
        },
        {
            "agent_id": "agent2",
            "framework": "eliza",
            "response": "Response 2",
            "processing_start": now + timedelta(seconds=0.5),
            "processing_end": now + timedelta(seconds=2),
            "total_time_seconds": 1.5,
            "votes": 0
        }
    ]
    
    # Create initial discussion
    discussion = create_discussion(topic_id, question, responses)
    assert discussion is not None
    
    # Update discussion with completed status
    updated = update_discussion(discussion["discussion_id"], responses, "completed")
    assert updated is not None
    
    # Verify timing information
    assert "processing_start" in updated
    assert "processing_end" in updated
    assert "total_processing_time" in updated
    
    # Convert stored times back to datetime for comparison
    start_time = datetime.fromisoformat(updated["processing_start"])
    end_time = datetime.fromisoformat(updated["processing_end"])
    total_time = float(updated["total_processing_time"])
    
    # Verify timing calculations
    assert start_time == now  # Should be earliest start time
    assert end_time == now + timedelta(seconds=2)  # Should be latest end time
    assert abs(total_time - 2.5) < 0.1  # Total should be sum of individual times
    
    # Test retrieving discussions
    discussions, total = get_discussions(topic_id)
    assert len(discussions) == 1
    retrieved = discussions[0]
    
    # Verify timing information is preserved
    assert "processing_start" in retrieved
    assert "processing_end" in retrieved
    assert "total_processing_time" in retrieved
    
    # Verify responses maintain timing information
    retrieved_responses = retrieved["responses"]
    if isinstance(retrieved_responses, str):
        retrieved_responses = json.loads(retrieved_responses)
    
    for resp in retrieved_responses:
        assert "processing_start" in resp
        assert "processing_end" in resp
        assert "total_time_seconds" in resp

def test_discussion_timing_error_handling():
    """Test handling of discussions with missing or invalid timing information"""
    topic_id = "test_topic_2"
    question = "Test question"
    
    # Create responses with missing timing information
    responses = [
        {
            "agent_id": "agent1",
            "framework": "rig",
            "response": "Response 1",
            "votes": 0
        },
        {
            "agent_id": "agent2",
            "framework": "eliza",
            "response": "Response 2",
            "votes": 0
        }
    ]
    
    # Create and update discussion
    discussion = create_discussion(topic_id, question, responses)
    updated = update_discussion(discussion["discussion_id"], responses, "completed")
    
    # Verify discussion is created without timing information
    assert updated is not None
    assert "processing_start" not in updated
    assert "processing_end" not in updated
    assert "total_processing_time" not in updated

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
