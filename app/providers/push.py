from app.providers.base import DeliveryProvider


class FirebasePushProvider(DeliveryProvider):
    async def send(
        self, recipient: str, content: str, metadata: dict | None = None
    ) -> bool:
        print(f"sending push notification to {recipient}:{content}")
        return True
