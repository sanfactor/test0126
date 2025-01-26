import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import json
from .redis_client import redis_client

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        self.redis = redis_client.client
        self.processing_interval = 60  # Process one discussion per minute
        self.queue_key = "discussion_queue"  # Global queue
        self.topic_queue_key = "topic_queue:{}"  # Format with topic_id
        self.last_processed_key = "last_processed:{}"  # Format with topic_id
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Initialize Redis connection
        try:
            self.redis.ping()
            self.logger.info("Redis connection successful")
            # Initialize queues if they don't exist
            if not self.redis.exists(self.queue_key):
                # Add a dummy entry that we'll remove immediately
                self.redis.zadd(self.queue_key, {"init": 0})
                self.redis.zrem(self.queue_key, "init")
                self.logger.info(f"Initialized queue {self.queue_key}")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise

        
        # Clear any stale data on initialization
        self._clear_stale_data()
        
    async def enqueue_discussion(self, topic_id: str, discussion_id: str, question: str) -> Tuple[bool, str]:
        """
        Add a discussion to the processing queue
        Returns: (success, message)
        """
        try:
            current_time = datetime.now().timestamp()
            topic_queue = self.topic_queue_key.format(topic_id)
            
            # Get current state atomically
            pipeline = self.redis.pipeline()
            pipeline.zcard(self.queue_key)  # Get global queue size
            pipeline.zcard(topic_queue)  # Get topic queue size
            pipeline.get(f"last_processed:{topic_id}")  # Get last processed time
            pipeline.zrange(topic_queue, -1, -1, withscores=True)  # Get last queued entry for topic
            global_size, topic_size, last_processed, last_entries = pipeline.execute()
            
            self.logger.info(f"Topic {topic_id} - Global size: {global_size}, Topic size: {topic_size}, Last processed: {last_processed}, Last entries: {last_entries}")
            
            # Create queue entry with processing time as score
            queue_entry = {
                "topic_id": topic_id,
                "discussion_id": discussion_id,
                "question": question,
                "queued_at": current_time,
                "sequence": global_size  # Use global sequence for FIFO ordering
            }
            entry_json = json.dumps(queue_entry)
            
            # Calculate processing time based on queue position
            processing_time = current_time
            if topic_size > 0:
                processing_time += self.processing_interval * topic_size
            
            self.logger.debug(f"Calculated processing time: {processing_time} for discussion {discussion_id}")
            
            # Use the calculated processing time as score
            if global_size == 0 or topic_size == 0:  # First ever discussion or first for topic
                processing_time = current_time  # Process immediately
                wait_time = 0
            else:
                # Get last processed time for this topic
                last_processed_key = self.last_processed_key.format(topic_id)
                last_processed = self.redis.get(last_processed_key)
                
                if last_processed:
                    last_time = float(last_processed)
                    # Ensure at least processing_interval seconds since last processing
                    processing_time = max(current_time, last_time + self.processing_interval)
                else:
                    processing_time = current_time + self.processing_interval
                
                # Add additional intervals for queued discussions
                if topic_size > 0:
                    processing_time += (topic_size - 1) * self.processing_interval
                
                wait_time = max(0, int(processing_time - current_time))
            
            # Add microsecond precision for FIFO ordering
            final_score = processing_time + (queue_entry["sequence"] / 1_000_000)
            
            # Add to queues atomically
            pipeline = self.redis.pipeline()
            pipeline.zadd(self.queue_key, {entry_json: final_score})
            pipeline.zadd(topic_queue, {entry_json: final_score})
            pipeline.execute()
            
            self.logger.info(f"Queued discussion {discussion_id} with score {final_score}")
            self.logger.debug(f"Queue entry: {queue_entry}")
            
            message = f"Discussion queued. Estimated wait time: {wait_time} seconds"
            return True, message
            
        except Exception as e:
            logger.error(f"Error enqueueing discussion: {str(e)}")
            return False, f"Error adding discussion to queue: {str(e)}"
            
    async def get_next_discussion(self) -> Optional[dict]:
        """Get the next discussion that's ready to be processed"""
        try:
            current_time = datetime.now().timestamp()
            self.logger.debug(f"Looking for next discussion at {current_time}")
            
            # Get earliest ready entries with scores <= current_time
            ready_entries = self.redis.zrangebyscore(
                self.queue_key,
                "-inf",  # Start from lowest score
                current_time,  # Up to current time
                withscores=True
            )
            
            if not ready_entries:
                self.logger.info("No entries in queue")
                return None
            
            # Sort entries by score (ascending) to ensure FIFO order
            sorted_entries = sorted(ready_entries, key=lambda x: x[1])
            self.logger.info(f"Found {len(sorted_entries)} entries in queue")
            
            # Try to process each entry in order
            for entry_json, score in sorted_entries:
                try:
                    entry_data = json.loads(entry_json)
                    topic_id = entry_data["topic_id"]
                    topic_queue = self.topic_queue_key.format(topic_id)
                    
                    # Check if entry is ready to be processed
                    if score > current_time:
                        self.logger.info(f"Next entry not ready yet (score={score}, current_time={current_time})")
                        return None
                    
                    # Check if this topic has been processed recently
                    last_processed_key = f"last_processed:{topic_id}"
                    last_processed = self.redis.get(last_processed_key)
                    if last_processed:
                        last_time = float(last_processed)
                        time_since_last = current_time - last_time
                        if time_since_last < self.processing_interval:
                            self.logger.info(
                                f"Topic {topic_id} was processed {time_since_last:.2f}s ago, "
                                f"waiting {(self.processing_interval - time_since_last):.2f}s more..."
                            )
                            continue
                    
                    # Remove from queues and update last processed time atomically
                    pipeline = self.redis.pipeline()
                    pipeline.zrem(self.queue_key, entry_json)
                    pipeline.zrem(topic_queue, entry_json)
                    pipeline.set(last_processed_key, str(current_time))
                    pipeline.execute()
                    
                    self.logger.info(f"Processing discussion {entry_data['discussion_id']} for topic {topic_id}")
                    return entry_data
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing queue entry: {str(e)}")
                    # Remove invalid entry
                    self.redis.zrem(self.queue_key, entry_json)
                    continue
            
            # No entries could be processed yet
            self.logger.info("No entries ready for processing after rate limit checks")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting next discussion: {str(e)}")
            return None
    async def get_queue_status(self, topic_id: str) -> Tuple[int, int]:
        """
        Get queue status for a topic
        Returns: (position in queue, estimated wait time in seconds)
        """
        try:
            current_time = datetime.now().timestamp()
            topic_queue = self.topic_queue_key.format(topic_id)
            
            # Get all entries for this topic
            entries = self.redis.zrange(topic_queue, 0, -1, withscores=True)
            if not entries:
                return 0, 0
            
            # Get last processed time
            last_processed = self.redis.get(self.last_processed_key.format(topic_id))
            if last_processed:
                last_time = float(last_processed)
                next_allowed = last_time + self.processing_interval
            else:
                next_allowed = current_time
            
            # Calculate position and wait time
            position = len(entries)
            if position > 0:
                # Add 1 second buffer to ensure we clear the interval
                wait_time = max(0, int(next_allowed - current_time + 1))
                # Add interval for each position after first
                wait_time += (position - 1) * self.processing_interval
            else:
                wait_time = 0
                
            return position, wait_time
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return 0, 0
            
    async def start_queue_processor(self):
        """Start the background queue processor"""
        while True:
            try:
                entry = await self.get_next_discussion()
                if entry:
                    logger.info(f"Processing discussion {entry['discussion_id']}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in queue processor: {str(e)}")
                await asyncio.sleep(5)

    def _clear_stale_data(self):
        """Clean up only expired processing entries from Redis"""
        try:
            current_time = datetime.now().timestamp()
            
            # Get all queue entries
            queue_entries = self.redis.zrange(self.queue_key, 0, -1, withscores=True)
            logger.info(f"Found {len(queue_entries)} existing queue entries")
            
            # Clean up only entries that are more than 5 minutes old
            for entry_json, score in queue_entries:
                try:
                    entry_data = json.loads(entry_json)
                    queued_at = entry_data.get("queued_at", 0)
                    if current_time - queued_at > 300:  # 5 minutes
                        self.redis.zrem(self.queue_key, entry_json)
                        topic_queue = self.topic_queue_key.format(entry_data["topic_id"])
                        self.redis.zrem(topic_queue, entry_json)
                        logger.info(f"Cleaned up stale queue entry: {entry_data['discussion_id']}")
                except Exception as e:
                    logger.error(f"Error processing queue entry: {str(e)}")
            
            # Clean up expired processing entries
            self.cleanup_expired_processing()
                
        except Exception as e:
            logger.error(f"Error cleaning up stale data: {str(e)}")
            
    def cleanup_expired_processing(self):
        """Clean up expired processing entries"""
        try:
            current_time = datetime.now().timestamp()
            
            # Get all last processed times
            last_processed_keys = self.redis.keys(self.last_processed_key.format("*"))
            
            # Remove expired entries
            for key in last_processed_keys:
                last_time = float(self.redis.get(key) or 0)
                if current_time - last_time > self.processing_interval * 2:
                    self.redis.delete(key)
                    logger.info(f"Cleaned up expired processing entry: {key}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up processing entries: {str(e)}")

queue_manager = QueueManager()
