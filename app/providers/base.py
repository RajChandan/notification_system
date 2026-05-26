from abc import ABC, abstractmethod


class DeliveryProvider(ABC):
    @abstractmethod
    async def send(
        self, recipient: str, content: str, metadata: dict | None = None
    ) -> bool:
        pass
