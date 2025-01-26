import sys
import os
import logging
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from main import app
from redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

@pytest.fixture(autouse=True)
async def clear_test_data():
    """Clear all test data from Redis before and after each test"""
    r = redis_client.client
    try:
        keys_to_delete = r.keys("*queue*") + r.keys("*topic*") + r.keys("*discussion*")
        if keys_to_delete:
            r.delete(*keys_to_delete)
        yield
    finally:
        keys_to_delete = r.keys("*queue*") + r.keys("*topic*") + r.keys("*discussion*")
        if keys_to_delete:
            r.delete(*keys_to_delete)

def test_create_discussion():
    """Test discussion creation and queueing"""
    # Create a test topic first
    topic_response = client.post(
        "/api/v1/topics",
        json={"title": "Test Topic", "description": "Test Description"}
    )
    assert topic_response.status_code == 200
    topic_id = topic_response.json()["topic_id"]
    
    # Create first discussion
    response = client.post(
        f"/api/v1/topics/{topic_id}/responses",
        json={"question": "Test question 1"}
    )
    assert response.status_code == 200
    discussion = response.json()
    assert discussion["status"] == "queued"
    assert discussion["queue_position"] == 1
    assert discussion["estimated_wait"] == 0  # First discussion should be immediate
    
    # Create second discussion
    response = client.post(
        f"/api/v1/topics/{topic_id}/responses",
        json={"question": "Test question 2"}
    )
    assert response.status_code == 200
    discussion = response.json()
    assert discussion["status"] == "queued"
    assert discussion["queue_position"] == 2
    assert discussion["estimated_wait"] >= 60  # Second discussion should wait
    
    # Verify placeholder responses
    for response in discussion["responses"]:
        assert "Processing..." in response["response"]
        assert response["votes"] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
