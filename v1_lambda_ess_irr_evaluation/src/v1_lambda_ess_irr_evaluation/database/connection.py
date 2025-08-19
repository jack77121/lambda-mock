import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Lambda-optimized database settings
POSTGRES_URL = os.getenv("POSTGRES_URL")

# Optimized connection pool settings for Lambda
# Smaller pool size for Lambda cold starts and memory constraints
engine = create_async_engine(
    POSTGRES_URL,
    echo=False,  # Disable SQL logging in production Lambda
    pool_size=2,  # Small pool for Lambda
    max_overflow=0,  # No overflow connections
    pool_pre_ping=True,  # Check connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
    connect_args={
        "server_settings": {
            "application_name": "lambda_ess_irr_evaluation",
        }
    },
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
