from app.models.notifications import Channel
from app.providers.email import SendGridEmailProvider
from app.providers.sms import TwilioSMSProvider
from app.providers.push import FirebasePushProvider


class DeliveryProviderFactory:

    @staticmethod
    def get_provider(channel: Channel):
        if channel == Channel.EMAIL:
            return SendGridEmailProvider()

        if channel == Channel.SMS:
            return TwilioSMSProvider()

        if channel == Channel.PUSH:
            return FirebasePushProvider()

        raise ValueError(f"Unsupported channel:{channel}")
