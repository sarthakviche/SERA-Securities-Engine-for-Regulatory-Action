import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/sera')

async def test():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        print("Tables:", res.fetchall())
        
        res = await conn.execute(text("SELECT typname FROM pg_type WHERE typname = 'embedding_status_enum'"))
        print("Enum exists:", res.fetchall())

asyncio.run(test())
