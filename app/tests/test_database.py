import sys
import os
import logging
from pathlib import Path
import pytest
from datetime import datetime
import json

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import create_topic, get_topics, get_topic, create_discussion, get_discussions, add_vote
from redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_test_data():
    """Clear all test data from Redis"""
    r = redis_client.client
    # Get all keys matching our test patterns
    keys = r.keys("topic:*") + r.keys("discussion:*") + r.keys("topic_discussions:*")
    if keys:
        r.delete(*keys)
    r.delete("topics")

def test_topic_operations():
    """Test topic creation and retrieval"""
    clear_test_data()
    
    # Test create_topic
    topic = create_topic("Test Topic", "Test Description")
    assert topic["title"] == "Test Topic"
    assert topic["description"] == "Test Description"
    assert "topic_id" in topic
    assert "created_at" in topic
    
    # Test get_topic
    retrieved_topic = get_topic(topic["topic_id"])
    assert retrieved_topic is not None
    assert retrieved_topic["title"] == topic["title"]
    assert retrieved_topic["description"] == topic["description"]
    
    # Test get_topics
    topics = get_topics()
    assert len(topics) == 1
    assert topics[0]["topic_id"] == topic["topic_id"]

def test_discussion_operations():
    """Test discussion creation, retrieval, and voting"""
    clear_test_data()
    
    # Create a test topic first
    topic = create_topic("Test Topic", "Test Description")
    
    # Test create_discussion
    responses = [
        {"agent_id": "agent1", "framework": "test", "response": "Response 1", "votes": 0},
        {"agent_id": "agent2", "framework": "test", "response": "Response 2", "votes": 0}
    ]
    discussion = create_discussion(topic["topic_id"], "Test Question", responses)
    assert discussion["topic_id"] == topic["topic_id"]
    assert discussion["question"] == "Test Question"
    assert len(discussion["responses"]) == 2
    
    # Test get_discussions
    discussions, total = get_discussions(topic["topic_id"])
    assert total == 1
    assert len(discussions) == 1
    assert discussions[0]["discussion_id"] == discussion["discussion_id"]
    assert len(discussions[0]["responses"]) == 2
    
    # Test voting
    success = add_vote(discussion["discussion_id"], "agent1")
    assert success is True
    
    # Verify vote was recorded
    discussions, _ = get_discussions(topic["topic_id"])
    responses = discussions[0]["responses"]
    agent1_response = next(r for r in responses if r["agent_id"] == "agent1")
    assert agent1_response["votes"] == 1

if __name__ == "__main__":
    try:
        test_topic_operations()
        logger.info("Topic operations tests passed!")
        
        test_discussion_operations()
        logger.info("Discussion operations tests passed!")
        
        logger.info("All database tests completed successfully!")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    finally:
        clear_test_data()
