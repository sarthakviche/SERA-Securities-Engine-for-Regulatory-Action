"""Judge demo: silently edit one audit row in Postgres, then click 'Verify chain integrity'.

    .venv/Scripts/python.exe scripts/tamper_demo.py           # tamper with the latest APPROVAL event
    .venv/Scripts/python.exe scripts/tamper_demo.py --undo    # restore the original text

Shows that even a DB administrator cannot quietly rewrite who approved what.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.core.db import AsyncSessionLocal  # noqa: E402

BACKUP = Path(__file__).with_name(".tamper_backup.json")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        if "--undo" in sys.argv:
            if not BACKUP.exists():
                print("Nothing to undo.")
                return
            b = json.loads(BACKUP.read_text())
            await db.execute(text("UPDATE audit_events SET actor=:a, detail=:d WHERE id=:i"), {"a": b["actor"], "d": b["detail"], "i": b["id"]})
            await db.commit()
            BACKUP.unlink()
            print(f"Restored audit event #{b['id']}.")
            return
        row = (await db.execute(text("SELECT id, actor, detail, title FROM audit_events WHERE kind='APPROVAL' ORDER BY id DESC LIMIT 1"))).first()
        if not row:
            print("No approval events yet - approve a gate first.")
            return
        BACKUP.write_text(json.dumps({"id": row.id, "actor": row.actor, "detail": row.detail}))
        await db.execute(text("UPDATE audit_events SET actor='Someone Else', detail='(edited after the fact)' WHERE id=:i"), {"i": row.id})
        await db.commit()
        print(f"Tampered with audit event #{row.id} ('{row.title}'). Now click 'Verify chain integrity' in the Audit Trail.")


asyncio.run(main())
