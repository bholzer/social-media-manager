import datetime
import uuid
from contextlib import asynccontextmanager
from unittest.mock import patch

from smm.models.post import Post
from smm.models.post_target import PostTarget, PostTargetStatus
from smm.models.social_account import Platform, SocialAccount
from smm.models.user import User
from smm.scheduler.scheduler import _poll_and_enqueue


class TestPollAndEnqueue:
    async def _setup_scheduled_post(self, session, scheduled_at):
        user = User(email=f"sched{uuid.uuid4().hex[:6]}@test.com", hashed_password="h")
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

        post = Post(
            user_id=user.id,
            content="Scheduled",
            scheduled_at=scheduled_at,
        )
        session.add(post)
        await session.flush()

        target = PostTarget(
            post_id=post.id,
            social_account_id=account.id,
            status=PostTargetStatus.SCHEDULED,
        )
        session.add(target)
        await session.commit()

        return target

    async def test_picks_up_due_targets(self, session):
        past = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=5)
        target = await self._setup_scheduled_post(session, past)

        @asynccontextmanager
        async def mock_session_ctx():
            yield session

        mock_task = type("MockTask", (), {"send": lambda self, x: None})()
        sends = []
        mock_task.send = lambda x: sends.append(x)

        with (
            patch(
                "smm.database.async_session_factory", return_value=mock_session_ctx()
            ),
            patch(
                "smm.scheduler.scheduler.publish_target_task", mock_task, create=True
            ),
            patch("smm.workers.tasks.publish_target_task", mock_task, create=True),
        ):
            await _poll_and_enqueue()

        await session.refresh(target)
        assert target.status == PostTargetStatus.PUBLISHING
        assert str(target.id) in sends

    async def test_ignores_future_targets(self, session):
        future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        target = await self._setup_scheduled_post(session, future)

        @asynccontextmanager
        async def mock_session_ctx():
            yield session

        sends = []
        mock_task = type("MockTask", (), {"send": lambda self, x: sends.append(x)})()

        with (
            patch(
                "smm.database.async_session_factory", return_value=mock_session_ctx()
            ),
            patch("smm.workers.tasks.publish_target_task", mock_task, create=True),
        ):
            await _poll_and_enqueue()

        await session.refresh(target)
        assert target.status == PostTargetStatus.SCHEDULED
        assert len(sends) == 0
