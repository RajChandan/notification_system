from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.dependencies import get_db
from app.services.notification_service import NotificationService
from app.schemas.notifications import NotificationCreateRequest

router = APIRouter()


@router.post("/")
async def send_notification(
    request: NotificationCreateRequest, db: AsyncSession = Depends(get_db)
):
    service = NotificationService(db)
    notification = await service.create_notification(request)
    print(f" created notification with payload: {request}")
    return {
        "notification_id": str(notification.notification_id),
        "status": notification.status.value,
    }
