import json
import time
from typing import Optional, Any
from app.core.config import settings

class InMemoryRedisFallback:
    def __init__(self):
        self._store = {}

    def _clean_expired(self):
        now = time.time()
        expired_keys = [k for k, v in self._store.items() if v["expires_at"] and v["expires_at"] < now]
        for k in expired_keys:
            del self._store[k]

    def set(self, name: str, value: Any, ex: Optional[int] = None) -> bool:
        self._clean_expired()
        expires_at = (time.time() + ex) if ex else None
        if not isinstance(value, str):
            value = json.dumps(value)
        self._store[name] = {"value": value, "expires_at": expires_at}
        return True

    def get(self, name: str) -> Optional[str]:
        self._clean_expired()
        item = self._store.get(name)
        if not item:
            return None
        return item["value"]

    def delete(self, name: str) -> bool:
        if name in self._store:
            del self._store[name]
            return True
        return False

    def incr(self, name: str) -> int:
        self._clean_expired()
        val = int(self.get(name) or 0) + 1
        item = self._store.get(name, {"expires_at": None})
        self._store[name] = {"value": str(val), "expires_at": item.get("expires_at")}
        return val

    def expire(self, name: str, time_sec: int):
        if name in self._store:
            self._store[name]["expires_at"] = time.time() + time_sec

class RedisManager:
    def __init__(self):
        self.client = None
        self.using_fallback = False
        self._init_client()

    def _init_client(self):
        try:
            import redis
            r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1.0)
            r.ping()
            self.client = r
            self.using_fallback = False
        except Exception:
            # Fallback gracefully to in-memory store for local testing
            self.client = InMemoryRedisFallback()
            self.using_fallback = True

    def set_seat_hold(self, event_id: int, seat_code: str, user_id: int, ttl_seconds: int = 600) -> bool:
        key = f"seat_hold:event:{event_id}:seat:{seat_code}"
        val = json.dumps({"user_id": user_id, "expires_at": time.time() + ttl_seconds})
        return bool(self.client.set(key, val, ex=ttl_seconds))

    def get_seat_hold(self, event_id: int, seat_code: str) -> Optional[dict]:
        key = f"seat_hold:event:{event_id}:seat:{seat_code}"
        res = self.client.get(key)
        if not res:
            return None
        try:
            return json.loads(res)
        except Exception:
            return None

    def release_seat_hold(self, event_id: int, seat_code: str) -> bool:
        key = f"seat_hold:event:{event_id}:seat:{seat_code}"
        return bool(self.client.delete(key))

    def acquire_lock(self, lock_name: str, ttl_seconds: int = 10) -> bool:
        key = f"lock:{lock_name}"
        if self.client.get(key):
            return False
        return bool(self.client.set(key, "LOCKED", ex=ttl_seconds))

    def release_lock(self, lock_name: str):
        key = f"lock:{lock_name}"
        self.client.delete(key)

    def check_rate_limit(self, identifier: str, limit: int = 10, window_sec: int = 600) -> bool:
        key = f"rate_limit:{identifier}"
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window_sec)
        return current <= limit

redis_manager = RedisManager()
