from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config_data.settings import settings
from loggers import get_logger
from .models import Base

logger = get_logger(__name__)

POSTGRES_DSN: str = settings.build_postgres_dsn()

engine = create_async_engine(POSTGRES_DSN,
                             echo=settings.db_echo,
                             pool_size=15,
                             max_overflow=10,
                             pool_timeout=30,
                             pool_recycle=60 * 30,  # Restart the pool after 30 minutes
                             )

_session_maker: sessionmaker[AsyncSession] | None = None


def init_async_session():
    logger.info(f"Initializing async session...")
    global _session_maker
    _session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # noqa


def get_session_maker() -> sessionmaker[AsyncSession]:
    if _session_maker is None:
        raise RuntimeError("SessionMaker not initialized. Did you forget to call init_async_session()?")
    return _session_maker


async def init_db():
    async with engine.begin() as conn:
        logger.info('Creating all tables')
        try:
            await conn.run_sync(Base.metadata.create_all)
            logger.info('Tables created')
        except Exception as e:
            logger.error(f"Error occurred: {e}")
