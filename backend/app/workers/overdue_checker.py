"""
Overdue Task Checker

Queries the `tasks` table for tasks that are past their due date and not yet
completed, then publishes a `task.overdue` DomainEvent for each.

Idempotency: the event's idempotency_key is scoped to the task + calendar day
("overdue:{task_id}:{YYYY-MM-DD}") so the same task only generates one
overdue notification per day even if the checker runs multiple times.

This module is intended to be called from a long-running asyncio loop inside
the FastAPI lifespan (see main.py).  It does NOT use Celery or Redis.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.core.events import DomainEvent
from app.core.notification_event_publisher import DEFAULT_USER_ID, NotificationAwareEventPublisher
from app.models.task import Task

logger = logging.getLogger("sera.workers.overdue_checker")


async def check_overdue_tasks() -> None:
    """
    Find all non-completed tasks that are past their due date and publish
    a task.overdue event for each.
    """
    today = date.today()
    logger.info("overdue checker running for date=%s", today)

    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(Task)
                .where(
                    Task.due_date < today,
                    Task.status.not_in(["Completed", "Overdue"]),
                )
            )
            result = await db.execute(stmt)
            overdue_tasks = list(result.scalars().all())

        logger.info("found %d overdue task(s)", len(overdue_tasks))

        publisher = NotificationAwareEventPublisher()

        for task in overdue_tasks:
            idempotency_key = f"overdue:{task.id}:{today.isoformat()}"
            event = DomainEvent(
                event_type="task.overdue",
                organization_id=DEFAULT_USER_ID,  # single-tenant org id
                workflow_id=task.workflow_id,
                payload={
                    "task_id": str(task.id),
                    "task_title": task.title,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                },
                idempotency_key=idempotency_key,
            )
            await publisher.publish(event)

    except Exception as exc:  # noqa: BLE001
        logger.error("overdue checker failed: %s", exc)


async def run_overdue_checker_loop(interval_seconds: int = 3600) -> None:
    """
    Infinite loop that calls check_overdue_tasks() every `interval_seconds`.
    Designed to be run as a background asyncio task from the FastAPI lifespan.
    """
    # Run immediately at startup so the first check happens within seconds
    await check_overdue_tasks()
    while True:
        await asyncio.sleep(interval_seconds)
        await check_overdue_tasks()
