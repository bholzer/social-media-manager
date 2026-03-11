import uuid
from unittest.mock import AsyncMock, patch

from smm.adapters.base import PublishResult
from smm.models.post import Post
from smm.models.post_target import PostTarget, PostTargetStatus
from smm.models.social_account import Platform, SocialAccount
from smm.models.user import User
from smm.services.publisher import publish_target


class TestPublishTarget:
    async def _setup(self, session):
        user = User(email=f"pub{uuid.uuid4().hex[:6]}@test.com", hashed_password="h")
        session.add(user)
        await session.commit()

        account = SocialAccount(
            user_id=user.id,
            platform=Platform.FACEBOOK,
            platform_user_id="fb_user",
            access_token="fb_token",
        )
        session.add(account)
        await session.commit()

        post = Post(user_id=user.id, content="Publish me")
        session.add(post)
        await session.flush()

        target = PostTarget(
            post_id=post.id,
            social_account_id=account.id,
            status=PostTargetStatus.PUBLISHING,
        )
        session.add(target)
        await session.commit()

        return target

    @patch("smm.services.publisher.AdapterRegistry")
    async def test_publish_success(self, mock_registry, session):
        target = await self._setup(session)

        mock_adapter = AsyncMock()
        mock_adapter.publish.return_value = PublishResult(platform_post_id="post_123")
        mock_registry.get.return_value = mock_adapter

        await publish_target(session, target.id)

        await session.refresh(target)
        assert target.status == PostTargetStatus.PUBLISHED
        assert target.platform_post_id == "post_123"
        assert target.published_at is not None

    @patch("smm.services.publisher.AdapterRegistry")
    async def test_publish_failure(self, mock_registry, session):
        target = await self._setup(session)

        mock_adapter = AsyncMock()
        mock_adapter.publish.side_effect = Exception("API error")
        mock_registry.get.return_value = mock_adapter

        await publish_target(session, target.id)

        await session.refresh(target)
        assert target.status == PostTargetStatus.FAILED
        assert "API error" in target.error_message

    async def test_publish_skips_non_publishing(self, session):
        target = await self._setup(session)
        target.status = PostTargetStatus.PUBLISHED
        await session.commit()

        await publish_target(session, target.id)

        await session.refresh(target)
        assert target.status == PostTargetStatus.PUBLISHED

    async def test_publish_nonexistent_target(self, session):
        # Should not raise
        await publish_target(session, uuid.uuid4())
