from redis.asyncio import Redis


class IdempotencyService:
    def __init__(self, redis: Redis):
        self.redis = redis

    def processing_key(self, notification_id: str) -> str:
        return f"notification:processing:{notification_id}"

    def sent_key(self, notification_id: str) -> str:
        return f"notification:sent:{notification_id}"

    async def is_sent(self, notification_id: str) -> str:
        return bool(await self.redis.exists(self.sent_key(notification_id)))

    async def acquire_processing_lock(
        self, notification_id: str, ttl_seconds: int = 300
    ) -> bool:
        acquired = await self.redis.set(
            self.processing_key(notification_id), "1", nx=True, ex=ttl_seconds
        )
        return bool(acquired)

    async def mark_sent(self, notification_id: str, ttl_seconds: int = 86400) -> None:
        await self.redis.set(self.sent_key(notification_id), "1", ex=ttl_seconds)

    async def release_processing_lock(self, notification_id: str) -> None:
        await self.redis.delete(self.processing_key(notification_id))
