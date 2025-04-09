import json


def get_cached_data(redis_client, key):
    value = redis_client.get(key)
    return json.loads(value) if value else None


def set_cache(redis_client, key, data, ttl: int = 120):
    redis_client.setex(key, ttl, json.dumps(data))