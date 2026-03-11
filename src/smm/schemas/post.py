import datetime
import uuid

from pydantic import BaseModel, Field

from smm.models.post_target import PostTargetStatus


class PostTargetCreate(BaseModel):
    social_account_id: uuid.UUID


class PostTargetResponse(BaseModel):
    id: uuid.UUID
    social_account_id: uuid.UUID
    status: PostTargetStatus
    published_at: datetime.datetime | None
    platform_post_id: str | None
    error_message: str | None

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    primary_link: str | None = None
    image_url: str | None = None
    scheduled_at: datetime.datetime | None = None
    targets: list[PostTargetCreate] = Field(min_length=1)


class PostUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    primary_link: str | None = None
    image_url: str | None = None
    scheduled_at: datetime.datetime | None = None


class PostResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    primary_link: str | None
    image_url: str | None
    scheduled_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    targets: list[PostTargetResponse] = []

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int
    size: int
