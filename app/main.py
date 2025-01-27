from datetime import datetime
from typing import List, Optional
import os
import logging
import uuid
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from .models import TopicCreate, Topic, Discussion, Vote, AgentResponse
from .database import (
    create_topic, get_topics, get_topic,
    create_discussion, update_discussion, get_discussions, add_vote
)
from .agents import RigAgent, ElizaAgent, SwarmsAgent
from .queue_manager import queue_manager

# Load environment variables
load_dotenv()

# Get port from environment variable or use default
PORT = int(os.getenv("PORT", "8001"))

app = FastAPI(title="agentgroup API")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize agents
rig_agent = RigAgent()
eliza_agent = ElizaAgent()
swarms_agent = SwarmsAgent()

# Start queue processor
@app.on_event("startup")
async def startup_event():
    """Start the queue processor on app startup"""
    asyncio.create_task(process_queued_discussions())

async def process_queued_discussions():
    """Background task to process queued discussions"""
    while True:
        try:
            entry = await queue_manager.get_next_discussion()
            if entry:
                topic_id = entry["topic_id"]
                discussion_id = entry["discussion_id"]
                question = entry["question"]
                
                logging.info(f"Processing discussion {discussion_id} for topic {topic_id}")
                logging.info(f"Question: {question}")
                
                # Process the discussion with all agents
                responses = []
                try:
                    for agent in [rig_agent, eliza_agent, swarms_agent]:
                        logging.info(f"Getting response from {agent.agent_id}")
                        response = await agent.get_timed_response(topic_id, question)
                        logging.info(f"Got response from {agent.agent_id}: {response}")
                        responses.append(response)
                    
                    # Update the discussion with real responses and processing times
                    logging.info(f"Updating discussion {discussion_id} with responses")
                    discussion = update_discussion(discussion_id, responses, status="completed")
                    logging.info(f"Successfully processed discussion {discussion_id}")
                except Exception as e:
                    logging.error(f"Error processing discussion {discussion_id}: {str(e)}")
                    # Update discussion with error status
                    error_responses = [
                        {
                            "agent_id": agent.agent_id,
                            "framework": agent.framework,
                            "response": "Error processing response",
                            "timestamp": datetime.now(),
                            "votes": 0,
                            "processing_start": None,
                            "processing_end": None,
                            "total_time_seconds": None
                        }
                        for agent in [rig_agent, eliza_agent, swarms_agent]
                    ]
                    update_discussion(discussion_id, error_responses, status="error")
                
        except Exception as e:
            logging.error(f"Error processing queued discussion: {str(e)}")
        
        await asyncio.sleep(1)  # Check queue every second

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/v1/topics", response_model=Topic)
async def create_new_topic(topic: TopicCreate):
    return create_topic(topic.title, topic.description)

@app.get("/api/v1/topics", response_model=List[Topic])
async def list_topics():
    return get_topics()

@app.post("/api/v1/topics/{topic_id}/responses", response_model=Discussion)
async def get_agent_responses(topic_id: str, question: dict):
    try:
        print(f"Received request for topic {topic_id} with question: {question}")
        
        topic = get_topic(topic_id)
        if not topic:
            print(f"Topic {topic_id} not found")
            raise HTTPException(status_code=404, detail="Topic not found")
        
        if "question" not in question:
            print("Missing question field in request")
            raise HTTPException(status_code=400, detail="Question field is required in request body")
        
        # Generate a new discussion ID
        discussion_id = str(uuid.uuid4())
        
        # Enqueue the discussion
        success, message = await queue_manager.enqueue_discussion(topic_id, discussion_id, question["question"])
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        # Get queue status
        position, wait_time = await queue_manager.get_queue_status(topic_id)
        
        # Create placeholder discussion with queued status
        placeholder_responses = [
            {
                "agent_id": agent.agent_id,
                "framework": agent.framework,
                "response": "Processing... Please check back in a moment.",
                "timestamp": datetime.now(),
                "votes": 0
            }
            for agent in [rig_agent, eliza_agent, swarms_agent]
        ]
        
        discussion = create_discussion(topic_id, question["question"], placeholder_responses)
        discussion["status"] = "queued"
        discussion["queue_position"] = position
        discussion["estimated_wait"] = wait_time
        
        print(f"Discussion queued successfully. Position: {position}, Wait time: {wait_time}s")
        return discussion
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in get_agent_responses: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/v1/topics/{topic_id}/discussions")
async def list_discussions(topic_id: str, page: int = 1, limit: int = 10):
    topic = get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    discussions, total = get_discussions(topic_id, page, limit)
    
    # For queued discussions, get current queue status
    for discussion in discussions:
        if discussion["status"] == "queued":
            position, wait_time = await queue_manager.get_queue_status(topic_id)
            discussion["queue_position"] = position
            discussion["estimated_wait"] = wait_time
    
    return {
        "discussions": discussions,
        "total": total,
        "page": page,
        "limit": limit
    }

@app.post("/api/v1/discussions/{discussion_id}/vote")
async def vote_for_response(discussion_id: str, vote: Vote):
    success = add_vote(discussion_id, vote.agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Discussion or agent not found")
    return {"status": "success", "message": "Vote recorded successfully"}
