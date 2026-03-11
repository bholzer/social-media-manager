import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from smm.adapters.registry import AdapterRegistry
from smm.models.post_target import PostTarget, PostTargetStatus


async def publish_target(session: AsyncSession, target_id: uuid.UUID) -> None:
    result = await session.execute(
        select(PostTarget)
        .options(
            selectinload(PostTarget.post),
            selectinload(PostTarget.social_account),
        )
        .where(PostTarget.id == target_id)
    )
    target = result.scalar_one_or_none()
    if target is None:
        return

    # Double-publish prevention: re-check status
    if target.status != PostTargetStatus.PUBLISHING:
        return

    adapter = AdapterRegistry.get(target.social_account.platform)

    try:
        publish_result = await adapter.publish(
            content=target.post.content,
            link=target.post.primary_link,
            image_url=target.post.image_url,
            access_token=target.social_account.access_token,
            platform_user_id=target.social_account.platform_user_id,
        )
        target.status = PostTargetStatus.PUBLISHED
        target.published_at = datetime.datetime.now(datetime.UTC)
        target.platform_post_id = publish_result.platform_post_id
    except Exception as e:
        target.status = PostTargetStatus.FAILED
        target.error_message = str(e)

    await session.commit()
