import redis
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisClient:
    _instance: Optional['RedisClient'] = None
    _redis = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._redis is None:
            self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection with retries"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self._redis = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._redis.ping()
            logger.info(f"Successfully connected to Redis at {redis_url}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis at {redis_url}: {str(e)}")
            raise

    @property
    def client(self):
        """Get Redis client instance"""
        if self._redis is None:
            self._initialize_redis()
        return self._redis

# Global Redis client instance
redis_client = RedisClient()
