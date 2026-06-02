import json
import time
from typing import Optional, Any
import threading
from config import settings

class MockRedisCache:
    def __init__(self):
        self._cache = {}
        self._expires = {}
        self._lock = threading.Lock()
        
    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key in self._cache:
                expiry = self._expires.get(key)
                if expiry and time.time() > expiry:
                    del self._cache[key]
                    del self._expires[key]
                    return None
                return self._cache[key]
            return None
            
    def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        with self._lock:
            self._cache[key] = value
            if ex:
                self._expires[key] = time.time() + ex
            elif key in self._expires:
                del self._expires[key]
                
    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)
            self._expires.pop(key, None)

# Initialize standard redis client if configured
redis_client = None
if not settings.is_mock_mode and settings.REDIS_URL:
    try:
        import redis
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception as e:
        print(f"Redis Cloud connection failed: {e}. Falling back to in-memory cache.")

# Fallback wrapper
class CacheService:
    def __init__(self):
        self.mock_cache = MockRedisCache()
        
    def get(self, key: str) -> Optional[Any]:
        if redis_client:
            try:
                data = redis_client.get(key)
                return json.loads(data) if data else None
            except Exception:
                pass
        return self.mock_cache.get(key)
        
    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> None:
        if redis_client:
            try:
                redis_client.set(key, json.dumps(value), ex=expire_seconds)
                return
            except Exception:
                pass
        self.mock_cache.set(key, json.dumps(value), ex=expire_seconds)
        
    def delete(self, key: str) -> None:
        if redis_client:
            try:
                redis_client.delete(key)
                return
            except Exception:
                pass
        self.mock_cache.delete(key)

cache_service = CacheService()
