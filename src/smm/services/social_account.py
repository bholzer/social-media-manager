import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smm.models.social_account import SocialAccount
from smm.schemas.social_account import SocialAccountCreate


class SocialAccountService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: uuid.UUID, data: SocialAccountCreate
    ) -> SocialAccount:
        account = SocialAccount(
            user_id=user_id,
            platform=data.platform,
            platform_user_id=data.platform_user_id,
            access_token=data.access_token,
            refresh_token=data.refresh_token,
            token_expires_at=data.token_expires_at,
        )
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def list(self, user_id: uuid.UUID) -> list[SocialAccount]:
        result = await self.session.execute(
            select(SocialAccount).where(SocialAccount.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get(
        self, user_id: uuid.UUID, account_id: uuid.UUID
    ) -> SocialAccount | None:
        result = await self.session.execute(
            select(SocialAccount).where(
                SocialAccount.id == account_id,
                SocialAccount.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, user_id: uuid.UUID, account_id: uuid.UUID) -> bool:
        account = await self.get(user_id, account_id)
        if account is None:
            return False
        await self.session.delete(account)
        await self.session.commit()
        return True
