import functools
import hashlib
import pickle
import redis
import os
import logging
from datetime import datetime, timedelta
import json
import threading
from typing import Any, Optional, Callable
import time

# Setup logging
logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.use_redis = False
        self.redis_client = None
        self.memory_cache = {}  # Fallback for when Redis isn't installed
        self.lock = threading.RLock()  # Thread-safe operations for in-memory cache
        
        # Try to connect to Redis
        if os.getenv("USE_REDIS", "False").lower() == "true":
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self.redis_client = redis.Redis.from_url(
                    redis_url,
                    socket_connect_timeout=1,
                    socket_timeout=2,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                self.redis_client.ping()  # Test connection
                self.use_redis = True
                logger.info("✅ Redis Cache Connected")
            except redis.ConnectionError:
                logger.warning("⚠️ Redis Connection Failed. Switching to In-Memory Cache.")
                self.use_redis = False
            except Exception as e:
                logger.warning(f"⚠️ Redis initialization failed: {e}. Switching to In-Memory Cache.")
                self.use_redis = False
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate a unique cache key based on function name and arguments
        """
        # Create a hash of the arguments to ensure uniqueness
        arg_str = str(args) + str(sorted(kwargs.items()))
        hash_key = hashlib.md5(arg_str.encode('utf-8')).hexdigest()
        return f"{func_name}:{hash_key}"
    
    def cache_result(self, ttl: int = 3600, key_prefix: str = ""):
        """
        Decorator to cache function results with TTL
        
        Args:
            ttl (int): Time to live in seconds
            key_prefix (str): Optional prefix for cache keys
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Generate unique cache key
                func_name = key_prefix + func.__name__ if key_prefix else func.__name__
                key = self._generate_key(func_name, args, kwargs)
                
                # Try to get from cache
                cached_result = self.get(key)
                if cached_result is not None:
                    logger.info(f"⚡ Cache HIT: {func_name}")
                    return cached_result
                
                # Execute function if not in cache
                logger.info(f"🔧 Cache MISS: {func_name}")
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Cache the result
                self.set(key, result, ttl)
                
                logger.info(f"⏱️ Function {func.__name__} executed in {execution_time:.3f}s and cached")
                return result
            return wrapper
        return decorator
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache
        
        Args:
            key (str): Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            if self.use_redis:
                # Redis logic
                cached_data = self.redis_client.get(key)
                if cached_data:
                    try:
                        return pickle.loads(cached_data)
                    except (pickle.PickleError, TypeError):
                        logger.warning(f"Failed to deserialize Redis cache for key: {key}")
                        return None
            else:
                # In-memory logic with thread safety
                with self.lock:
                    if key in self.memory_cache:
                        data, expiry = self.memory_cache[key]
                        if datetime.now() < expiry:
                            return data
                        else:
                            # Clean up expired entry
                            del self.memory_cache[key]
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set a value in cache
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (int): Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.use_redis:
                # Redis logic
                serialized_value = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized_value)
                return True
            else:
                # In-memory logic with thread safety
                with self.lock:
                    self.memory_cache[key] = (
                        value, 
                        datetime.now() + timedelta(seconds=ttl)
                    )
                return True
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache
        
        Args:
            key (str): Cache key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.use_redis:
                result = self.redis_client.delete(key)
                return result > 0
            else:
                with self.lock:
                    if key in self.memory_cache:
                        del self.memory_cache[key]
                        return True
                return False
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.use_redis:
                # Delete all keys in current database
                keys = self.redis_client.keys('*')
                if keys:
                    self.redis_client.delete(*keys)
                return True
            else:
                with self.lock:
                    self.memory_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Cache CLEAR error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache
        
        Args:
            key (str): Cache key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            if self.use_redis:
                return self.redis_client.exists(key) > 0
            else:
                with self.lock:
                    return key in self.memory_cache and datetime.now() < self.memory_cache[key][1]
        except Exception as e:
            logger.error(f"Cache EXISTS error for key {key}: {e}")
            return False
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics
        """
        try:
            if self.use_redis:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'connected': self.use_redis,
                    'total_keys': info.get('db0', {}).get('keys', 0),
                    'memory_used': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0)
                }
            else:
                with self.lock:
                    active_keys = 0
                    for key, (data, expiry) in self.memory_cache.items():
                        if datetime.now() < expiry:
                            active_keys += 1
                    
                    return {
                        'type': 'memory',
                        'connected': True,
                        'total_keys': len(self.memory_cache),
                        'active_keys': active_keys,
                        'expired_keys': len(self.memory_cache) - active_keys
                    }
        except Exception as e:
            logger.error(f"Cache STATS error: {e}")
            return {
                'type': 'error',
                'error': str(e)
            }
    
    def cleanup_expired(self) -> int:
        """
        Manually cleanup expired in-memory cache entries
        
        Returns:
            int: Number of expired entries removed
        """
        if self.use_redis:
            # Redis handles expiration automatically
            return 0
        
        with self.lock:
            now = datetime.now()
            expired_keys = [
                key for key, (data, expiry) in self.memory_cache.items()
                if now >= expiry
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            return len(expired_keys)
    
    def get_memory_usage(self) -> int:
        """
        Get approximate memory usage of in-memory cache
        
        Returns:
            int: Memory usage in bytes
        """
        if self.use_redis:
            return 0  # Redis memory usage is handled by Redis
        
        with self.lock:
            try:
                import sys
                total_size = 0
                for key, (data, expiry) in self.memory_cache.items():
                    total_size += sys.getsizeof(key)
                    total_size += sys.getsizeof(data)
                    total_size += sys.getsizeof(expiry)
                return total_size
            except Exception:
                return 0

# Global cache manager instance
cache_manager = CacheManager()

# Convenience functions for easy access
def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """
    Convenience function to cache results
    
    Args:
        ttl (int): Time to live in seconds
        key_prefix (str): Optional prefix for cache keys
    """
    return cache_manager.cache_result(ttl, key_prefix)

def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    return cache_manager.get(key)

def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache"""
    return cache_manager.set(key, value, ttl)

def delete_cache(key: str) -> bool:
    """Delete value from cache"""
    return cache_manager.delete(key)

def clear_cache() -> bool:
    """Clear all cache"""
    return cache_manager.clear()

def cache_exists(key: str) -> bool:
    """Check if key exists in cache"""
    return cache_manager.exists(key)

def get_cache_stats() -> dict:
    """Get cache statistics"""
    return cache_manager.get_stats()