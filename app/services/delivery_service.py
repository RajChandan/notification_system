from app.models.utils import Channel
from app.providers.factory import DeliveryProviderFactory


class DeliveryService:
    def __init__(self, provider_factory=DeliveryProviderFactory):
        self.provider_factory = provider_factory

    async def deliver(self, event: dict) -> bool:
        channel = Channel(event["channel"])

        provider = self.provider_factory.get_provider(channel)

        return await provider.send(
            recipient=event["recipient"],
            content=event["content"],
            metadata=event.get("metadata", {}),
        )
