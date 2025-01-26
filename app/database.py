from datetime import datetime
import uuid
from typing import Dict, List, Optional
import json
from .redis_client import redis_client
from json import JSONEncoder

class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

r = redis_client.client

def create_topic(title: str, description: str) -> dict:
    topic_id = str(uuid.uuid4())
    topic = {
        "topic_id": topic_id,
        "title": title,
        "description": description,
        "created_at": datetime.now().isoformat()
    }
    # Store topic in Redis hash and add to topics set
    r.hset(f"topic:{topic_id}", mapping=topic)
    r.sadd("topics", topic_id)
    return topic

def get_topics() -> List[dict]:
    topic_ids = r.smembers("topics")
    topics = []
    for topic_id in topic_ids:
        topic_data = r.hgetall(f"topic:{topic_id}")
        if topic_data:
            topics.append(topic_data)
    return topics

def get_topic(topic_id: str) -> Optional[dict]:
    topic_data = r.hgetall(f"topic:{topic_id}")
    return topic_data if topic_data else None

def create_discussion(topic_id: str, question: str, responses: List[dict], status: str = "pending", discussion_id: str = None) -> dict:
    if discussion_id is None:
        discussion_id = str(uuid.uuid4())
    
    # Ensure timing fields exist in responses
    for response in responses:
        if "processing_start" not in response:
            response["processing_start"] = None
        if "processing_end" not in response:
            response["processing_end"] = None
        if "total_time_seconds" not in response:
            response["total_time_seconds"] = None
    
    discussion = {
        "discussion_id": discussion_id,
        "topic_id": topic_id,
        "question": question,
        "created_at": datetime.now().isoformat(),
        "status": status
    }
    # Serialize responses with datetime handling
    discussion["responses"] = json.dumps(responses, cls=DateTimeEncoder)
    
    # Store discussion in Redis hash
    r.hset(f"discussion:{discussion_id}", mapping=discussion)
    # Add to topic's discussions sorted set with timestamp as score
    score = datetime.fromisoformat(discussion["created_at"]).timestamp()
    r.zadd(f"topic_discussions:{topic_id}", {discussion_id: score})
    
    # Return discussion with deserialized responses
    discussion["responses"] = responses
    return discussion

def update_discussion(discussion_id: str, responses: List[dict], status: str = "completed") -> dict:
    """Update an existing discussion with new responses and status"""
    discussion_key = f"discussion:{discussion_id}"
    discussion_data = r.hgetall(discussion_key)
    if not discussion_data:
        return None
    
    # Calculate aggregate timing information
    total_processing_time = 0
    earliest_start = None
    latest_end = None
    
    for response in responses:
        if "total_time_seconds" in response:
            total_processing_time += response["total_time_seconds"]
        
        if "processing_start" in response:
            start_time = response["processing_start"]
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if earliest_start is None or start_time < earliest_start:
                earliest_start = start_time
                
        if "processing_end" in response:
            end_time = response["processing_end"]
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            if latest_end is None or end_time > latest_end:
                latest_end = end_time
    
    # Update responses and status with datetime handling
    discussion_data["responses"] = json.dumps(responses, cls=DateTimeEncoder)
    discussion_data["status"] = status
    
    # Add timing metadata
    if earliest_start and latest_end:
        discussion_data["processing_start"] = earliest_start.isoformat()
        discussion_data["processing_end"] = latest_end.isoformat()
        discussion_data["total_processing_time"] = str(total_processing_time)
    
    # Store updated discussion
    r.hset(discussion_key, mapping=discussion_data)
    
    # Return updated discussion with deserialized responses
    discussion_data["responses"] = responses
    return discussion_data

def get_discussions(topic_id: str, page: int = 1, limit: int = 10) -> tuple[List[dict], int]:
    # Get total count of discussions for this topic
    total = r.zcard(f"topic_discussions:{topic_id}")
    
    # Calculate start and end indices for pagination
    start = (page - 1) * limit
    end = start + limit - 1  # -1 because Redis includes the end index
    
    # Get discussion IDs for this page, sorted by creation time (newest first)
    discussion_ids = r.zrevrange(f"topic_discussions:{topic_id}", start, end)
    
    discussions = []
    for discussion_id in discussion_ids:
        discussion_data = r.hgetall(f"discussion:{discussion_id}")
        if discussion_data:
            # Check if responses is a string (JSON) and deserialize if needed
            if isinstance(discussion_data.get("responses"), str):
                responses = json.loads(discussion_data["responses"])
                # Ensure timing information is included in each response
                for response in responses:
                    if "processing_start" not in response:
                        response["processing_start"] = None
                    if "processing_end" not in response:
                        response["processing_end"] = None
                    if "total_time_seconds" not in response:
                        response["total_time_seconds"] = None
                discussion_data["responses"] = responses
            discussions.append(discussion_data)
    
    return discussions, total

def add_vote(discussion_id: str, agent_id: str) -> bool:
    discussion_data = r.hgetall(f"discussion:{discussion_id}")
    if not discussion_data:
        return False
    
    # Handle both string and list responses
    responses = discussion_data["responses"]
    if isinstance(responses, str):
        responses = json.loads(responses)
    
    updated = False
    for response in responses:
        if response["agent_id"] == agent_id:
            response["votes"] = response.get("votes", 0) + 1
            updated = True
            break
    
    if updated:
        # Update the discussion with new vote count
        discussion_data["responses"] = json.dumps(responses)
        r.hset(f"discussion:{discussion_id}", mapping=discussion_data)
        return True
    
    return False
