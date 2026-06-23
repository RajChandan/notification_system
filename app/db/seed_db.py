import asyncio
from datetime import datetime

from app.db.session import AsyncSessionLocal
from app.models.notifications import Channel
from app.models.templates import Template, TemplateType


async def seed_templates():
    async with AsyncSessionLocal() as db:
        templates = [
            Template(
                template_name="welcome_email",
                channel=Channel.EMAIL,
                template_type=TemplateType.TRANSACTIONAL,
                content="Hello {{name}}, welcome to our platform!",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Template(
                template_name="otp_sms",
                channel=Channel.SMS,
                template_type=TemplateType.TRANSACTIONAL,
                content="Your OTP is {{otp}}. It is valid for {{minutes}} minutes.",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Template(
                template_name="order_push",
                channel=Channel.PUSH,
                template_type=TemplateType.TRANSACTIONAL,
                content="Your order {{order_id}} has been shipped.",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Template(
                template_name="promo_email",
                channel=Channel.EMAIL,
                template_type=TemplateType.PROMOTIONAL,
                content="Hi {{name}}, get {{discount}}% off on your next purchase!",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        db.add_all(templates)
        await db.commit()

        print("Templates seeded successfully")


if __name__ == "__main__":
    asyncio.run(seed_templates())
