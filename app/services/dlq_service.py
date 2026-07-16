import json
from datetime import datetime

from aiokafka import AIOKafkaProducer


class DLQService:
    def __init__(self, producer: AIOKafkaProducer, topic: str):
        self.producer = producer
        self.topic = topic

    async def publish(self, event: dict, reason: str, retry_count: int) -> None:
        notification_id = str(event.get("notification_id", "unknown"))
        payload = {
            **event,
            "dlq_reason": reason,
            "retry_count": retry_count,
            "failed_at": datetime.utcnow().isoformat(),
        }

        await self.producer.send_and_wait(
            self.topic,
            key=notification_id.encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
        )
