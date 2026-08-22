import json
from typing import Optional, Dict, Any
from app.core.redis import redis_manager

def get_idempotency_cache(idempotency_key: str) -> Optional[Dict[str, Any]]:
    if not idempotency_key:
        return None
    val = redis_manager.client.get(f"idempotency:{idempotency_key}")
    if not val:
        return None
    try:
        return json.loads(val)
    except Exception:
        return None

def set_idempotency_cache(idempotency_key: str, payload: Dict[str, Any], ttl_seconds: int = 86400):
    if not idempotency_key:
        return
    redis_manager.client.set(f"idempotency:{idempotency_key}", json.dumps(payload), ex=ttl_seconds)
