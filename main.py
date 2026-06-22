from fastapi import FastAPI
from app.api.notifications_routes import router

app = FastAPI(title="Notification Service", version="1.0.0")

app.include_router(router, prefix="/api/v1/notifications", tags=["notifications"])
