from abc import ABC, abstractmethod
from datetime import datetime
import uuid

class BaseAgent(ABC):
    def __init__(self):
        self.agent_id = str(uuid.uuid4())
        self.framework = "base"

    @abstractmethod
    async def process_question(self, topic: str, question: str) -> str:
        """Process a question and return a response"""
        pass

    async def get_timed_response(self, topic: str, question: str) -> dict:
        """Get a response with timing information"""
        start_time = datetime.now()
        try:
            response = await self.process_question(topic, question)
            end_time = datetime.now()
            return {
                "agent_id": self.agent_id,
                "framework": self.framework,
                "response": response,
                "timestamp": datetime.now(),
                "votes": 0,
                "processing_start": start_time,
                "processing_end": end_time,
                "total_time_seconds": (end_time - start_time).total_seconds()
            }
        except Exception as e:
            end_time = datetime.now()
            return {
                "agent_id": self.agent_id,
                "framework": self.framework,
                "response": f"Error: {str(e)}",
                "timestamp": datetime.now(),
                "votes": 0,
                "processing_start": start_time,
                "processing_end": end_time,
                "total_time_seconds": (end_time - start_time).total_seconds()
            }
