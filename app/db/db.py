import os
import asyncio

from fastapi import FastAPI
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from contextlib import asynccontextmanager

from datetime import datetime

from app.db.models import Lot
from .base import Base

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def check_expired_lots():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Lot).where(Lot.status == "running", Lot.end_time <= datetime.now()).with_for_update()
                )
                lots = result.scalars().all()

                now = datetime.now()

                for lot in lots:
                    if lot.end_time <= now:
                        lot.status = "ended"

                await session.commit()
        except Exception as e:
            print(f"Error in check_expired_lots: {e}")

        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    task = asyncio.create_task(check_expired_lots())
    print("✅ App started")


    yield

    task.cancel()
    # SHUTDOWN
    print("🛑 App stopped")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
