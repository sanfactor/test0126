import sys
import os
import logging
from pathlib import Path
import pytest
from datetime import datetime, timedelta

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents import RigAgent, ElizaAgent, SwarmsAgent
from agents.base import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockAgent(BaseAgent):
    """Mock agent for testing timing functionality"""
    def __init__(self, delay: float = 0.1):
        super().__init__()
        self.framework = "mock"
        self.delay = delay
        
    async def process_question(self, topic: str, question: str) -> str:
        import asyncio
        await asyncio.sleep(self.delay)  # Simulate processing time
        return "Mock response"

@pytest.mark.asyncio
async def test_timing_success():
    """Test timing information is recorded for successful responses"""
    agent = MockAgent(delay=0.1)
    response = await agent.get_timed_response("test_topic", "test_question")
    
    # Check all timing fields are present
    assert "processing_start" in response
    assert "processing_end" in response
    assert "total_time_seconds" in response
    
    # Verify timing data types
    assert isinstance(response["processing_start"], datetime)
    assert isinstance(response["processing_end"], datetime)
    assert isinstance(response["total_time_seconds"], float)
    
    # Verify timing values are reasonable
    assert response["total_time_seconds"] >= 0.1  # Should be at least our delay
    assert response["total_time_seconds"] < 1.0  # Shouldn't take too long
    assert response["processing_end"] > response["processing_start"]

@pytest.mark.asyncio
async def test_timing_error():
    """Test timing information is recorded even when errors occur"""
    class ErrorAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            self.framework = "error"
            
        async def process_question(self, topic: str, question: str) -> str:
            raise Exception("Test error")
    
    agent = ErrorAgent()
    response = await agent.get_timed_response("test_topic", "test_question")
    
    # Check timing fields are present
    assert "processing_start" in response
    assert "processing_end" in response
    assert "total_time_seconds" in response
    
    # Verify error response
    assert "Error:" in response["response"]
    
    # Verify timing is still valid
    assert response["processing_end"] > response["processing_start"]
    assert response["total_time_seconds"] >= 0

@pytest.mark.asyncio
async def test_real_agents():
    """Test timing functionality with actual agent implementations"""
    agents = [RigAgent(), ElizaAgent(), SwarmsAgent()]
    topic = "Test Topic"
    question = "What is the meaning of life?"
    
    for agent in agents:
        response = await agent.get_timed_response(topic, question)
        
        # Check timing fields
        assert "processing_start" in response
        assert "processing_end" in response
        assert "total_time_seconds" in response
        
        # Verify timing data types
        assert isinstance(response["processing_start"], datetime)
        assert isinstance(response["processing_end"], datetime)
        assert isinstance(response["total_time_seconds"], float)
        
        # Basic sanity checks
        assert response["processing_end"] > response["processing_start"]
        assert response["total_time_seconds"] >= 0
        
        # Log timing information
        logger.info(f"{agent.framework} agent took {response['total_time_seconds']:.3f} seconds")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
