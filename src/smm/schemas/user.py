import datetime
import uuid

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
