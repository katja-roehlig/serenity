from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join("data", "serenity.db")}"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)  # echo=True - für Infos!

async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with async_session() as session:
        yield session
