import asyncio
import uuid
from dotenv import load_dotenv
load_dotenv()

from app.pipeline.runner import run_pipeline
from app.core.db import AsyncSessionLocal
from sqlalchemy import text

async def seed_document(document_id: str):
    doc_uuid = uuid.uuid5(uuid.NAMESPACE_URL, document_id)
    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            INSERT INTO regulatory_documents (id, circular_number, title) 
            VALUES (:id, :circular_number, :title)
            ON CONFLICT (id) DO NOTHING
        """), {"id": doc_uuid, "circular_number": document_id, "title": "Test Title"})
        await db.commit()

async def verify_db():
    async with AsyncSessionLocal() as db:
        print("\n--- OBLIGATIONS ---")
        res1 = await db.execute(text("SELECT id, workflow_id, title FROM obligations;"))
        for row in res1:
            print(f"id: {row[0]}, workflow_id: {row[1]}, title: {row[2]}")
            
        print("\n--- TASKS ---")
        res2 = await db.execute(text("SELECT id, workflow_id, obligation_id, title FROM tasks;"))
        for row in res2:
            print(f"id: {row[0]}, workflow_id: {row[1]}, obligation_id: {row[2]}, title: {row[3]}")

async def main():
    job_id = "test-job-e2e"
    document_id = "SEBI-CIRC-2026-08-03-103314"
    print("Seeding parent document in DB...")
    await seed_document(document_id)
    
    print("Starting pipeline...")
    await run_pipeline(job_id, document_id)
    print("Pipeline completed.")
    
    print("Verifying DB...")
    await verify_db()

if __name__ == "__main__":
    asyncio.run(main())
