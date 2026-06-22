from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/notification_db"
DATABASE_URL = "sqlite+aiosqlite:///./notification.db"

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)
