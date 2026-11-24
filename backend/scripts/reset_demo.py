"""Wipe workflow data (keeps org profile) so the demo starts fresh. Circulars are re-seeded on next backend start."""
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
    shutil.rmtree(settings.DATA_DIR / "evidence", ignore_errors=True)
    print("SERA demo data reset.")


asyncio.run(main())
