import uuid

import pytest

from smm.models.post import Post
from smm.models.post_target import PostTarget, PostTargetStatus
from smm.models.social_account import Platform, SocialAccount
from smm.models.user import User


class TestUserModel:
    async def test_create_user(self, session):
        user = User(email="user@test.com", hashed_password="hashed")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "user@test.com"
        assert user.created_at is not None

    async def test_user_email_unique(self, session):
        import sqlalchemy

        user1 = User(email="dup@test.com", hashed_password="h1")
        user2 = User(email="dup@test.com", hashed_password="h2")
        session.add(user1)
        await session.commit()
        session.add(user2)
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await session.commit()


class TestSocialAccountModel:
    async def test_create_social_account(self, session):
        user = User(email="sa@test.com", hashed_password="h")
        session.add(user)
        await session.commit()

        account = SocialAccount(
            user_id=user.id,
            platform=Platform.FACEBOOK,
            platform_user_id="12345",
            access_token="tok",
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)

        assert account.id is not None
        assert account.platform == Platform.FACEBOOK

    async def test_cascade_delete_user_deletes_accounts(self, session):
        user = User(email="cascade@test.com", hashed_password="h")
        session.add(user)
        await session.commit()

        account = SocialAccount(
            user_id=user.id,
            platform=Platform.INSTAGRAM,
            platform_user_id="99",
            access_token="tok",
        )
        session.add(account)
        await session.commit()

        await session.delete(user)
        await session.commit()

        from sqlalchemy import select

        result = await session.execute(
            select(SocialAccount).where(SocialAccount.id == account.id)
        )
        assert result.scalar_one_or_none() is None


class TestPlatformEnum:
    def test_platform_values(self):
        assert Platform.FACEBOOK.value == "facebook"
        assert Platform.INSTAGRAM.value == "instagram"
        assert Platform.TWITTER.value == "twitter"
        assert Platform.LINKEDIN.value == "linkedin"


class TestPostTargetStatusEnum:
    def test_status_values(self):
        assert PostTargetStatus.DRAFT.value == "draft"
        assert PostTargetStatus.SCHEDULED.value == "scheduled"
        assert PostTargetStatus.PUBLISHING.value == "publishing"
        assert PostTargetStatus.PUBLISHED.value == "published"
        assert PostTargetStatus.FAILED.value == "failed"


class TestPostModel:
    async def test_create_post_with_targets(self, session):
        user = User(email="post@test.com", hashed_password="h")
        session.add(user)
        await session.commit()

        account = SocialAccount(
            user_id=user.id,
            platform=Platform.FACEBOOK,
            platform_user_id="1",
            access_token="tok",
        )
        session.add(account)
        await session.commit()

        post = Post(user_id=user.id, content="Hello world")
        session.add(post)
        await session.flush()

        target = PostTarget(
            post_id=post.id,
            social_account_id=account.id,
            status=PostTargetStatus.DRAFT,
        )
        session.add(target)
        await session.commit()

        await session.refresh(post)
        assert post.id is not None
        assert post.created_at is not None

    async def test_cascade_delete_post_deletes_targets(self, session):
        user = User(email="pcd@test.com", hashed_password="h")
        session.add(user)
        await session.commit()

        account = SocialAccount(
            user_id=user.id,
            platform=Platform.FACEBOOK,
            platform_user_id="2",
            access_token="tok",
        )
        session.add(account)
        await session.commit()

        post = Post(user_id=user.id, content="Delete me")
        session.add(post)
        await session.flush()

        target = PostTarget(
            post_id=post.id,
            social_account_id=account.id,
            status=PostTargetStatus.DRAFT,
        )
        session.add(target)
        await session.commit()

        target_id = target.id
        await session.delete(post)
        await session.commit()

        from sqlalchemy import select

        result = await session.execute(
            select(PostTarget).where(PostTarget.id == target_id)
        )
        assert result.scalar_one_or_none() is None
