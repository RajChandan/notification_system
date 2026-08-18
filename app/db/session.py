from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://notification_user:notification_password@localhost:5433/notification_db"
# DATABASE_URL = "sqlite+aiosqlite:///./notification.db"

engine = create_async_engine(
    DATABASE_URL, echo=False, pool_pre_ping=True, pool_size=10, max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)
