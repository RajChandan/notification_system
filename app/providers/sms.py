from app.providers.base import DeliveryProvider


class TwilioSMSProvider(DeliveryProvider):
    async def send(
        self, recipient: str, content: str, metadata: dict | None = None
    ) -> bool:
        print(f"sending sms to {recipient}:{content}")
        return True
