import sys
import os
import logging
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test basic Redis connection and operations"""
    try:
        # Get Redis client
        r = redis_client.client
        
        # Test basic operations
        logger.info("Testing Redis SET operation...")
        r.set("test_key", "test_value")
        
        logger.info("Testing Redis GET operation...")
        value = r.get("test_key")
        assert value == "test_value", f"Expected 'test_value', got {value}"
        
        logger.info("Testing Redis DEL operation...")
        r.delete("test_key")
        value = r.get("test_key")
        assert value is None, f"Expected None, got {value}"
        
        logger.info("All Redis tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Redis test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_redis_connection()
