import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smm.dependencies import get_current_user, get_session
from smm.models.social_account import SocialAccount
from smm.models.user import User
from smm.schemas.social_account import SocialAccountCreate, SocialAccountResponse

router = APIRouter()


@router.post(
    "/", response_model=SocialAccountResponse, status_code=status.HTTP_201_CREATED
)
async def create_social_account(
    data: SocialAccountCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    account = SocialAccount(
        user_id=current_user.id,
        platform=data.platform,
        platform_user_id=data.platform_user_id,
        access_token=data.access_token,
        refresh_token=data.refresh_token,
        token_expires_at=data.token_expires_at,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


@router.get("/", response_model=list[SocialAccountResponse])
async def list_social_accounts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(SocialAccount).where(SocialAccount.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.get("/{account_id}", response_model=SocialAccountResponse)
async def get_social_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    await session.delete(account)
    await session.commit()
