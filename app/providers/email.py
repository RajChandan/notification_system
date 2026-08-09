import logging
import time

from app.core.log_utils mask_email
from app.providers.base import DeliveryProvider


logger = logging.getLogger(__name__)

class SendGridEmailProvider(DeliveryProvider):
    async def send(
        self, recipient: str, content: str, metadata: dict | None = None
    ) -> bool:
        start_time = time.perf_counter()
        logger.info("Email delivery started",extra={"event":"provider_delivery_started","channel":"email","recipient":mask_email(recipient)})
        print(f"sending mail  to {recipient} : {content}")

        try:
            success = True

        except Exception:
            logger.exception("Email provider failed",extra={"event":"provider_delivery_failed","channel":"email","recipient":mask_email(recipient)})
            raise

        duration_ms = (time.perf_counter()-start_time) * 1000

        logger.info("Email provider completed",extra={"event":"provider_delivery_completed","channel":"email","recipient":mask_email(recipient),"success":success,"duration_ms":round(duration_ms,2)})
        return success
