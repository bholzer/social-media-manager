import datetime
import uuid

from pydantic import BaseModel, Field

from smm.models.social_account import Platform


class SocialAccountCreate(BaseModel):
    platform: Platform
    platform_user_id: str = Field(min_length=1)
    access_token: str = Field(min_length=1)
    refresh_token: str | None = None
    token_expires_at: datetime.datetime | None = None


class SocialAccountResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    platform: Platform
    platform_user_id: str
    token_expires_at: datetime.datetime | None

    model_config = {"from_attributes": True}
