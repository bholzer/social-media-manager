import uuid

import pytest
from pydantic import ValidationError

from smm.schemas.auth import LoginRequest, RegisterRequest
from smm.schemas.post import PostCreate, PostTargetCreate, PostUpdate


class TestRegisterRequest:
    def test_valid(self):
        r = RegisterRequest(email="a@b.com", password="12345678")
        assert r.email == "a@b.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="12345678")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="short")


class TestLoginRequest:
    def test_valid(self):
        r = LoginRequest(email="a@b.com", password="pass")
        assert r.email == "a@b.com"


class TestPostCreate:
    def test_valid(self):
        p = PostCreate(
            content="Hello",
            targets=[PostTargetCreate(social_account_id=uuid.uuid4())],
        )
        assert p.content == "Hello"
        assert len(p.targets) == 1

    def test_empty_content(self):
        with pytest.raises(ValidationError):
            PostCreate(
                content="",
                targets=[PostTargetCreate(social_account_id=uuid.uuid4())],
            )

    def test_no_targets(self):
        with pytest.raises(ValidationError):
            PostCreate(content="Hello", targets=[])

    def test_content_too_long(self):
        with pytest.raises(ValidationError):
            PostCreate(
                content="x" * 5001,
                targets=[PostTargetCreate(social_account_id=uuid.uuid4())],
            )


class TestPostUpdate:
    def test_partial_update(self):
        p = PostUpdate(content="Updated")
        assert p.content == "Updated"
        assert p.scheduled_at is None
