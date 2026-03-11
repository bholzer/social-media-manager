import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from smm.models.post import Post
from smm.models.post_target import PostTarget, PostTargetStatus
from smm.models.social_account import SocialAccount
from smm.schemas.post import PostCreate, PostUpdate


class PostService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, data: PostCreate) -> Post:
        # Verify all target social accounts belong to the user
        account_ids = [t.social_account_id for t in data.targets]
        result = await self.session.execute(
            select(SocialAccount).where(
                SocialAccount.id.in_(account_ids),
                SocialAccount.user_id == user_id,
            )
        )
        valid_accounts = {a.id for a in result.scalars().all()}
        if len(valid_accounts) != len(account_ids):
            raise ValueError(
                "One or more social accounts not found or not owned by user"
            )

        status = (
            PostTargetStatus.SCHEDULED if data.scheduled_at else PostTargetStatus.DRAFT
        )

        post = Post(
            user_id=user_id,
            content=data.content,
            primary_link=data.primary_link,
            image_url=data.image_url,
            scheduled_at=data.scheduled_at,
        )
        self.session.add(post)
        await self.session.flush()

        for target_data in data.targets:
            target = PostTarget(
                post_id=post.id,
                social_account_id=target_data.social_account_id,
                status=status,
            )
            self.session.add(target)

        await self.session.commit()
        return await self.get(user_id, post.id)

    async def get(self, user_id: uuid.UUID, post_id: uuid.UUID) -> Post | None:
        result = await self.session.execute(
            select(Post)
            .options(selectinload(Post.targets))
            .where(Post.id == post_id, Post.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        size: int = 20,
        status: PostTargetStatus | None = None,
    ) -> tuple[list[Post], int]:
        query = (
            select(Post)
            .options(selectinload(Post.targets))
            .where(Post.user_id == user_id)
        )
        count_query = select(func.count(Post.id)).where(Post.user_id == user_id)

        if status:
            query = query.join(Post.targets).where(PostTarget.status == status)
            count_query = count_query.join(Post.targets).where(
                PostTarget.status == status
            )

        query = (
            query.order_by(Post.created_at.desc()).offset((page - 1) * size).limit(size)
        )

        result = await self.session.execute(query)
        posts = list(result.scalars().unique().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return posts, total

    async def update(
        self, user_id: uuid.UUID, post_id: uuid.UUID, data: PostUpdate
    ) -> Post | None:
        post = await self.get(user_id, post_id)
        if post is None:
            return None

        # Don't allow updates if any target is published
        if any(t.status == PostTargetStatus.PUBLISHED for t in post.targets):
            raise ValueError("Cannot update a post with published targets")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(post, key, value)

        # If scheduled_at changed, update target statuses
        if "scheduled_at" in update_data:
            new_status = (
                PostTargetStatus.SCHEDULED
                if data.scheduled_at
                else PostTargetStatus.DRAFT
            )
            for target in post.targets:
                if target.status in (
                    PostTargetStatus.DRAFT,
                    PostTargetStatus.SCHEDULED,
                ):
                    target.status = new_status

        await self.session.commit()
        return await self.get(user_id, post_id)

    async def delete(self, user_id: uuid.UUID, post_id: uuid.UUID) -> bool:
        post = await self.get(user_id, post_id)
        if post is None:
            return False
        await self.session.delete(post)
        await self.session.commit()
        return True
