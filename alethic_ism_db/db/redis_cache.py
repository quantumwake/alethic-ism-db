from typing import Optional, List

import redis
from core.base_model import SessionMessage

from .processor_state_db_storage import SessionDatabaseStorage


class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(host=host, port=port, db=db)
        self.cache_ttl = 3600  # Cache TTL in seconds (e.g., 1 hour)

    def get(self, key: str) -> Optional[str]:
        return self.redis_client.get(key)

    def set(self, key: str, value: str):
        self.redis_client.setex(key, self.cache_ttl, value)

    def delete(self, key: str):
        self.redis_client.delete(key)


class CachedSessionStorage(SessionDatabaseStorage):

    def __init__(self, cache: RedisCache):
        self.cache = cache

    def fetch_session_messages(self, user_id: str, session_id: str) -> Optional[List[SessionMessage]]:
        # // TODO need to validate this user is part of session id.

        cache_key = f"session_messages:{session_id}"
        cached_data = self.cache.get(cache_key)

        if cached_data:
            return [SessionMessage.parse_raw(msg) for msg in json.loads(cached_data)]

        messages = self.database.fetch_session_messages(session_id)

        if messages:
            cached_data = json.dumps([msg.json() for msg in messages])
            self.cache.set(cache_key, cached_data)

        return messages

    def insert_session_message(self, user_id: str, session_id: str, content: str) -> SessionMessage:
        message = self.database.insert_session_message(user_id, session_id, content)

        # Invalidate the cache for this session
        cache_key = f"session_messages:{session_id}"
        self.cache.delete(cache_key)
        return message
