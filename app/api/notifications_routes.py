from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.dependencies import get_db
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("/")
async def send_notification(payload: dict, db: AsyncSession = Depends(get_db)):
    service = NotificationService(db)

    return await service.create_notification(
        user_id="123", template_type="transactional", channel="email", payload=payload
    )
