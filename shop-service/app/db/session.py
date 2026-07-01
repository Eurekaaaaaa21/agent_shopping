from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

# Auto-adapt: PostgreSQL for prod, SQLite for local dev without Docker
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    async_database_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
else:
    async_database_url = db_url

engine = create_async_engine(
    async_database_url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False, "timeout": 30} if "sqlite" in async_database_url else {},
)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize SQLite pragmas for better concurrency"""
    if "sqlite" in async_database_url:
        import aiosqlite
        # Enable WAL mode for better concurrent read/write
        async with aiosqlite.connect(
            async_database_url.replace("sqlite+aiosqlite:///", "")
        ) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA busy_timeout=5000")
            await db.execute("PRAGMA synchronous=NORMAL")


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
