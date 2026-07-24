from app.providers.base import DeliveryProvider


class SendGridEmailProvider(DeliveryProvider):
    async def send(
        self, recipient: str, content: str, metadata: dict | None = None
    ) -> bool:
        print(f"sending mail  to {recipient} : {content}")
        return True
