import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.notifications_routes import router
from app.core.logging import configure_logging
from app.db.session import engine

configure_logging(log_level="INFO")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Notification service starting up ...", extra={"event": "application_starting"}
    )
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        logger.info(
            "Database connection established ", extra={"event": "database_connected"}
        )

        yield

    finally:
        logger.info(
            "Notification service shutting down ... ",
            extra={"event": "application_shutdown"},
        )

        await engine.dispose()

        logger.info(
            "Database connection closed", extra={"event": "database_disconnected"}
        )


app = FastAPI(title="Notification Service", version="1.0.0", lifespan=lifespan)

app.include_router(router, prefix="/api/v1/notifications", tags=["notifications"])
