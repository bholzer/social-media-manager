import asyncio
import datetime
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from smm.models.post import Post
from smm.models.post_target import PostTarget, PostTargetStatus

logger = logging.getLogger(__name__)


def poll_and_enqueue() -> None:
    asyncio.run(_poll_and_enqueue())


async def _poll_and_enqueue() -> None:
    from smm.database import async_session_factory

    async with async_session_factory() as session:
        now = datetime.datetime.now(datetime.UTC)
        result = await session.execute(
            select(PostTarget)
            .join(Post)
            .where(
                PostTarget.status == PostTargetStatus.SCHEDULED,
                Post.scheduled_at <= now,
            )
        )
        targets = result.scalars().all()

        if not targets:
            return

        # Atomically transition to PUBLISHING
        for target in targets:
            target.status = PostTargetStatus.PUBLISHING
        await session.commit()

        # Enqueue Dramatiq tasks
        from smm.workers.tasks import publish_target_task

        for target in targets:
            logger.info(f"Enqueuing publish for target {target.id}")
            publish_target_task.send(str(target.id))


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(poll_and_enqueue, "interval", seconds=30, id="poll_and_enqueue")
    scheduler.start()
    logger.info("Scheduler started - polling every 30s")
    return scheduler


def stop_scheduler(scheduler: BackgroundScheduler) -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
