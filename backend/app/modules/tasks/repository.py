import uuid
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task

class TaskRepository:
    
    async def get_by_workflow(self, db: AsyncSession, workflow_id: uuid.UUID) -> List[Task]:
        stmt = select(Task).where(Task.workflow_id == workflow_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_tasks(
        self, 
        db: AsyncSession, 
        workflow_id: uuid.UUID, 
        tasks_data: List[Dict[str, Any]]
    ) -> List[Task]:
        """
        Upserts tasks for a workflow. For simplicity in the prototype,
        we delete existing tasks for this workflow and recreate them to ensure idempotency.
        """
        # Fetch existing tasks for this workflow
        existing_stmt = select(Task).where(Task.workflow_id == workflow_id)
        result = await db.execute(existing_stmt)
        existing_tasks = list(result.scalars().all())
        
        # Delete existing tasks
        for t in existing_tasks:
            await db.delete(t)
            
        await db.flush()

        new_tasks = []
        for t_data in tasks_data:
            title = t_data.get("title", "")
            if not title:
                continue
                
            # Maps to "status" in runner mock output if present
            status_val = t_data.get("status", "Pending")
            # Map obligation_id from the source_obligation_id provided by the LLM
            obligation_id_str = t_data.get("source_obligation_id")
            obligation_id = uuid.UUID(obligation_id_str) if obligation_id_str else None
            
            task = Task(
                workflow_id=workflow_id,
                obligation_id=obligation_id,
                title=title,
                status=status_val
            )
            db.add(task)
            new_tasks.append(task)
            
        await db.flush()
        return new_tasks

task_repository = TaskRepository()
