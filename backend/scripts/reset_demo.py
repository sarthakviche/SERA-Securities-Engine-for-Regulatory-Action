"""Wipe workflow data (keeps org profile) so the demo starts fresh. Circulars in downloads/ are re-registered."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shutil

from sqlalchemy import text

from app.core.config import settings
from app.core.db import AsyncSessionLocal


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(text("TRUNCATE tasks, obligations, workflow_documents, regulatory_documents, "
                              "audit_events, notifications RESTART IDENTITY CASCADE"))
        await db.commit()
    from app.engine.service import seed_local_pdfs
    async with AsyncSessionLocal() as db:
        n = await seed_local_pdfs(db)
        await db.commit()
    print(f"Re-registered {n} circular(s) from downloads/.")
    shutil.rmtree(settings.DATA_DIR / "evidence", ignore_errors=True)
    print("SERA demo data reset.")


asyncio.run(main())
