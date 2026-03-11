import asyncio
import uuid

import dramatiq

from smm.workers.broker import redis_broker  # noqa: F401 - registers the broker


@dramatiq.actor(max_retries=3, min_backoff=1000, max_backoff=60000)
def publish_target_task(target_id: str) -> None:
    asyncio.run(_publish(target_id))


async def _publish(target_id: str) -> None:
    from smm.database import async_session_factory
    from smm.services.publisher import publish_target

    async with async_session_factory() as session:
        await publish_target(session, uuid.UUID(target_id))
