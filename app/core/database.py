import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

# -----------------------------
# LOAD ENV
# -----------------------------
load_dotenv()

# -----------------------------
# DATABASE CONFIG
# -----------------------------
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", ""))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"mysql+aiomysql://{DB_USERNAME}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -----------------------------
# ASYNC ENGINE (STABLE CONFIG)
# -----------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,

    # 🔥 REQUIRED FOR MYSQL STABILITY (Windows Safe)
    pool_pre_ping=True,     # checks connection before use
    pool_recycle=1800,      # recycle before MySQL timeout
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)

# -----------------------------
# ASYNC SESSION FACTORY
# -----------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# -----------------------------
# FASTAPI DEPENDENCY
# -----------------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
