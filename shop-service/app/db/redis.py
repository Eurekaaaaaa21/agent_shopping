import redis.asyncio as redis
import json
import logging
from typing import Optional, Any
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

redis_client: Optional[redis.Redis] = None


async def init_redis():
    global redis_client
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed, cache will be degraded: {e}")
        redis_client = None


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def is_redis_available() -> bool:
    return redis_client is not None


async def cache_get(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.warning(f"Redis GET error for key {key}: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 600):
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
    except Exception as e:
        logger.warning(f"Redis SET error for key {key}: {e}")


async def cache_delete(key: str):
    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Redis DELETE error for key {key}: {e}")


async def cache_delete_pattern(pattern: str):
    if not redis_client:
        return
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis DELETE pattern error for {pattern}: {e}")
