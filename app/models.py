from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class TopicCreate(BaseModel):
    title: str
    description: str

class Topic(TopicCreate):
    topic_id: str
    created_at: datetime

class AgentResponse(BaseModel):
    agent_id: str
    framework: str
    response: str
    timestamp: datetime
    votes: int = 0
    processing_start: Optional[datetime] = None
    processing_end: Optional[datetime] = None
    total_time_seconds: Optional[float] = None

class Discussion(BaseModel):
    discussion_id: str
    topic_id: str
    question: str
    responses: List[AgentResponse]
    created_at: datetime
    status: str = "pending"  # pending, queued, completed
    queue_position: Optional[int] = None
    estimated_wait: Optional[int] = None

class Vote(BaseModel):
    agent_id: str
