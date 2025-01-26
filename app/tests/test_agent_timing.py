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

# Configure pytest-asyncio
pytest.asyncio_fixture_loop_scope = "function"

@pytest.mark.asyncio
async def test_rig_agent_timing():
    """Test timing information for Rig agent"""
    agent = RigAgent()
    response = await agent.get_timed_response("test_topic", "What is the performance impact?")
    
    assert response["framework"] == "rig"
    assert isinstance(response["processing_start"], datetime)
    assert isinstance(response["processing_end"], datetime)
    assert isinstance(response["total_time_seconds"], float)
    assert response["total_time_seconds"] >= 0
    assert "performance" in response["response"].lower()
    logger.info(f"Rig agent response time: {response['total_time_seconds']:.3f}s")

@pytest.mark.asyncio
async def test_eliza_agent_timing():
    """Test timing information for Eliza agent"""
    agent = ElizaAgent()
    response = await agent.get_timed_response("test_topic", "How does the implementation work?")
    
    assert response["framework"] == "eliza"
    assert isinstance(response["processing_start"], datetime)
    assert isinstance(response["processing_end"], datetime)
    assert isinstance(response["total_time_seconds"], float)
    assert response["total_time_seconds"] >= 0
    assert "implementation" in response["response"].lower()
    logger.info(f"Eliza agent response time: {response['total_time_seconds']:.3f}s")

@pytest.mark.asyncio
async def test_swarms_agent_timing():
    """Test timing information for Swarms agent"""
    agent = SwarmsAgent()
    response = await agent.get_timed_response("test_topic", "What about governance?")
    
    assert response["framework"] == "swarms"
    assert isinstance(response["processing_start"], datetime)
    assert isinstance(response["processing_end"], datetime)
    assert isinstance(response["total_time_seconds"], float)
    assert response["total_time_seconds"] >= 0
    assert "governance" in response["response"].lower()
    logger.info(f"Swarms agent response time: {response['total_time_seconds']:.3f}s")

@pytest.mark.asyncio
async def test_agent_error_timing():
    """Test timing information is recorded even during errors"""
    class ErrorAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            self.framework = "error_test"
            
        async def process_question(self, topic: str, question: str) -> str:
            raise Exception("Simulated error")
    
    agent = ErrorAgent()
    response = await agent.get_timed_response("test_topic", "This will error")
    
    assert response["framework"] == "error_test"
    assert isinstance(response["processing_start"], datetime)
    assert isinstance(response["processing_end"], datetime)
    assert isinstance(response["total_time_seconds"], float)
    assert response["total_time_seconds"] >= 0
    assert "Error:" in response["response"]
    logger.info(f"Error agent response time: {response['total_time_seconds']:.3f}s")

@pytest.mark.asyncio
async def test_concurrent_agent_timing():
    """Test timing information when running agents concurrently"""
    agents = [RigAgent(), ElizaAgent(), SwarmsAgent()]
    topic = "Test Topic"
    question = "What are the key considerations?"
    
    import asyncio
    responses = await asyncio.gather(*[
        agent.get_timed_response(topic, question)
        for agent in agents
    ])
    
    for response in responses:
        assert isinstance(response["processing_start"], datetime)
        assert isinstance(response["processing_end"], datetime)
        assert isinstance(response["total_time_seconds"], float)
        assert response["total_time_seconds"] >= 0
        logger.info(f"{response['framework']} concurrent response time: {response['total_time_seconds']:.3f}s")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
