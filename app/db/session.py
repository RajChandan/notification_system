from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/notification_db"


engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=40, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)
